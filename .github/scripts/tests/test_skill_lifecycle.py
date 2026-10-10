from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import skill_lifecycle as lifecycle
import publish_skills as publishing


def repository(root: Path) -> Path:
    (root / '.github').mkdir()
    lifecycle.write_json(root / '.github/skill-catalog.json', {'categories': {'financial': {'name': 'Finance', 'description': 'Example', 'repository': 'AISA-skills/example'}}})
    lifecycle.write_json(root / 'maintenance/upstreams.json', {'docs': {'type': 'docs', 'url': 'https://example.com/docs.md'}})
    lifecycle.write_json(root / 'maintenance/reviews.json', {})
    (root / 'README.md').write_text('<!-- catalog:start -->\n<!-- catalog:end -->\n')
    skill = root / 'financial/example'
    skill.mkdir(parents=True)
    (skill / 'SKILL.md').write_text('---\nname: example\ndescription: Example\nmetadata:\n  version: "1.0.0"\n---\n# Example\n')
    lifecycle.write_json(skill / 'skill.json', {'schema_version': 1, 'owner': '@owner', 'languages': [],
        'runtime': {}, 'entrypoints': [], 'checks': {}, 'upstreams': ['docs']})
    (skill / 'CHANGELOG.md').write_text('# Changelog\n\n## 1.0.0\n\n- Baseline.\n')
    (skill.parent / 'LICENSE').write_text('Example license\n')
    for args in (('init', '-b', 'main'), ('config', 'user.name', 'Tests'), ('config', 'user.email', 'tests@example.com'), ('add', '.'), ('commit', '-m', 'Baseline')):
        lifecycle.git(root, *args)
    return skill


class VersionPolicyTests(unittest.TestCase):
    def test_changes_require_version_and_changelog(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = repository(root)
            base = lifecycle.git(root, 'rev-parse', 'HEAD')
            (skill / 'README.md').write_text('New instructions\n')
            self.assertIn('strictly higher version', '\n'.join(lifecycle.validate(root, base)))
            self.assertEqual(lifecycle.bump(root, 'financial/example', 'patch', 'Fix instructions'), '1.0.1')
            self.assertEqual(lifecycle.validate(root, base), [])

    def test_category_license_change_requires_version(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = repository(root)
            (skill.parent / 'LICENSE').write_text('Changed license\n')
            self.assertIn('strictly higher version', '\n'.join(lifecycle.validate(root, 'HEAD')))

    def test_released_version_cannot_be_rewritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = repository(root)
            lifecycle.git(root, 'tag', 'skills/example/v1.0.0')
            (skill / 'README.md').write_text('Changed\n')
            self.assertIn('immutable version', '\n'.join(lifecycle.validate(root)))

    def test_versions_are_independent_and_missing_metadata_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = repository(root)
            self.assertEqual(lifecycle.validate(root, 'HEAD'), [])
            (skill / 'SKILL.md').write_text('---\nname: example\ndescription: Example\n---\n')
            self.assertIn('metadata.version', '\n'.join(lifecycle.validate(root)))

    def test_unknown_upstream_and_external_entrypoint_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = repository(root)
            manifest = lifecycle.read_json(skill / 'skill.json')
            manifest['upstreams'] = ['missing']
            lifecycle.write_json(skill / 'skill.json', manifest)
            self.assertIn('known upstream', '\n'.join(lifecycle.validate(root)))
            manifest['upstreams'] = ['docs']
            manifest['entrypoints'] = ['../../README.md']
            lifecycle.write_json(skill / 'skill.json', manifest)
            self.assertIn('unsafe entrypoint', '\n'.join(lifecycle.validate(root)))

    def test_malformed_review_cannot_break_the_scheduled_report_after_merge(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository(root)
            lifecycle.write_json(root / 'maintenance/reviews.json', {'financial/example': {'verified_at': 'invalid'}})
            self.assertIn('maintenance/reviews.json', '\n'.join(lifecycle.validate(root)))


class RuntimeAndBundleTests(unittest.TestCase):
    def test_archives_are_reproducible_and_include_license_and_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository(root)
            first = lifecycle.bundle(root, root / 'out1')
            second = lifecycle.bundle(root, root / 'out2')
            self.assertEqual(first, second)
            self.assertEqual((root / 'out1/example-1.0.0.tar.gz').read_bytes(), (root / 'out2/example-1.0.0.tar.gz').read_bytes())
            import tarfile
            with tarfile.open(root / 'out1/example-1.0.0.tar.gz') as archive:
                self.assertIn('LICENSE', archive.getnames())
                self.assertIn('example/SKILL.md', archive.getnames())
                self.assertEqual({item.mtime for item in archive.getmembers()}, {0})
            self.assertEqual(first[0]['source_commit'], lifecycle.git(root, 'rev-parse', 'HEAD'))

    def test_typescript_requires_locked_build_and_built_entrypoint(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = repository(root)
            (skill / 'client.ts').write_text('const answer: number = 42;\n')
            manifest = lifecycle.read_json(skill / 'skill.json')
            manifest['languages'] = ['typescript']
            manifest['runtime'] = {'node': '22'}
            lifecycle.write_json(skill / 'skill.json', manifest)
            self.assertIn('package-lock.json', '\n'.join(lifecycle.validate(root)))

    def test_isolated_build_output_must_match_shipped_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = repository(root)
            (skill / 'client.mjs').write_text('console.log("portable");\n')
            manifest = lifecycle.read_json(skill / 'skill.json')
            manifest['languages'] = ['javascript']
            manifest['runtime'] = {'node': '22'}
            manifest['checks'] = {'build': [['{python}', '-c', 'from pathlib import Path; Path("client.mjs").write_text("changed")']]}
            lifecycle.write_json(skill / 'skill.json', manifest)
            with self.assertRaisesRegex(ValueError, 'build output differs'):
                lifecycle.run_checks(root)
            self.assertEqual((skill / 'client.mjs').read_text(), 'console.log("portable");\n')
            manifest['checks'] = {'test': [['node', 'client.mjs']]}
            lifecycle.write_json(skill / 'skill.json', manifest)
            lifecycle.run_checks(root)

    def test_workspace_dependency_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = repository(root)
            lifecycle.write_json(skill / 'package.json', {'version': '1.0.0', 'engines': {'node': '>=22'}, 'dependencies': {'other': 'workspace:*'}})
            lifecycle.write_json(skill / 'package-lock.json', {'version': '1.0.0', 'packages': {'': {'version': '1.0.0'}}})
            self.assertIn('source workspace', '\n'.join(lifecycle.validate(root)))

    def test_catalog_counts_are_generated_and_checked(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository(root)
            with self.assertRaisesRegex(ValueError, 'counts are stale'):
                lifecycle.generate_catalog(root, check=True)
            lifecycle.generate_catalog(root)
            lifecycle.generate_catalog(root, check=True)
            self.assertIn('**1 skills**', (root / 'README.md').read_text())


class PublicationTests(unittest.TestCase):
    def test_empty_export_cannot_delete_a_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(publishing.subprocess, 'run') as run:
                with self.assertRaisesRegex(ValueError, 'empty export'):
                    publishing.publish_directory(Path(directory), 'owner/example', 'main', 'test-token', 'Empty')
                run.assert_not_called()

    def test_category_history_is_preserved_and_unchanged_exports_are_skipped(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source'
            source.mkdir()
            (source / 'README.md').write_text('First\n')
            remote = root / 'remote.git'
            subprocess.run(['git', 'init', '--bare', str(remote)], check=True, capture_output=True)
            real_run = subprocess.run
            def local_remote(command, **kwargs):
                if command[:4] == ['git', 'remote', 'add', 'origin']:
                    command = command[:-1] + [str(remote)]
                return real_run(command, **kwargs)
            with patch.object(publishing.subprocess, 'run', side_effect=local_remote):
                self.assertTrue(publishing.publish_directory(source, 'owner/example', 'main', 'test-token', 'First', {'source_commit': 'a'}))
                self.assertFalse(publishing.publish_directory(source, 'owner/example', 'main', 'test-token', 'No change', {'source_commit': 'b'}))
                (source / 'README.md').write_text('Second\n')
                self.assertTrue(publishing.publish_directory(source, 'owner/example', 'main', 'test-token', 'Second', {'source_commit': 'c'}))
            self.assertEqual(lifecycle.git(remote, 'rev-list', '--count', 'main'), '2')
            self.assertIn('c', lifecycle.git(remote, 'show', 'main:SOURCE.json'))

    def test_new_release_is_draft_until_assets_are_uploaded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository(root)
            lifecycle.bundle(root, root / 'out')
            calls = []
            def gh(command, **kwargs):
                calls.append(command)
                missing = command[1] == 'api' and command[2].endswith('v1.0.0')
                return subprocess.CompletedProcess(command, 1 if missing else 0, '', 'HTTP 404' if missing else '')
            with patch.object(publishing.subprocess, 'run', side_effect=gh):
                publishing.publish_releases(root / 'out', 'owner/example')
            self.assertIn('--method', calls[1])
            self.assertIn('--draft', calls[2])
            self.assertIn('--verify-tag', calls[2])
            self.assertIn('--draft=false', calls[3])

    def test_auth_failure_does_not_create_release(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository(root)
            lifecycle.bundle(root, root / 'out')
            with patch.object(publishing.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, '', 'HTTP 401')) as run:
                with self.assertRaisesRegex(RuntimeError, 'inspect release'):
                    publishing.publish_releases(root / 'out', 'owner/example')
                run.assert_called_once()

    def test_altered_validated_archive_is_rejected_before_network_access(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository(root)
            lifecycle.bundle(root, root / 'out')
            (root / 'out/example-1.0.0.tar.gz').write_bytes(b'altered')
            with patch.object(publishing.subprocess, 'run') as run:
                with self.assertRaisesRegex(ValueError, 'checksum'):
                    publishing.publish_releases(root / 'out', 'owner/example')
                run.assert_not_called()

    def test_interrupted_draft_upload_is_resumed_without_overwriting_published_release(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository(root)
            release = lifecycle.bundle(root, root / 'out')[0]
            calls = []
            def gh(command, **kwargs):
                calls.append(command)
                if command[1] == 'api':
                    output = json.dumps({'object': {'type': 'commit', 'sha': release['source_commit']}})
                elif command[2] == 'view':
                    output = json.dumps({'isDraft': True})
                elif command[2] == 'download':
                    destination = Path(command[command.index('--dir') + 1])
                    lifecycle.write_json(destination / 'example-1.0.0.json', release)
                    output = ''
                else:
                    output = ''
                return subprocess.CompletedProcess(command, 0, output, '')
            with patch.object(publishing.subprocess, 'run', side_effect=gh):
                publishing.publish_releases(root / 'out', 'owner/example')
            self.assertIn('--clobber', calls[2])
            self.assertIn('--draft=false', calls[-1])
            self.assertFalse(any('create' in command for command in calls))


if __name__ == '__main__':
    unittest.main()
