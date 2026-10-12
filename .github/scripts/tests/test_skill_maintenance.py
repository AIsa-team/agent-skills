from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import skill_lifecycle as lifecycle
import skill_maintenance as maintenance
from test_skill_lifecycle import repository


class FreshnessTests(unittest.TestCase):
    def test_unassigned_ownership_warns_even_after_a_current_review(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = repository(root)
            now = datetime.now(timezone.utc).isoformat()
            manifest = lifecycle.read_json(skill / 'skill.json')
            manifest['owner'] = lifecycle.UNASSIGNED_OWNER
            lifecycle.write_json(skill / 'skill.json', manifest)
            state = {'sources': {'docs': {'status': 'ok', 'digest': 'a', 'baseline_digest': 'a', 'observed_at': now}}}
            maintenance.record_review(root, 'financial/example', state, 'Verified contract', now)
            row = maintenance.report(root, state, now)[0]
            self.assertEqual(row['owner'], 'unassigned')
            self.assertEqual(row['warnings'], ['owner unassigned'])
            self.assertIn('owner unassigned', maintenance.markdown([row], now))
            manifest['owner'] = '@maintainer'
            lifecycle.write_json(skill / 'skill.json', manifest)
            maintenance.record_review(root, 'financial/example', state, 'Verified after assignment', now)
            assigned = maintenance.report(root, state, now)[0]
            self.assertEqual(assigned['owner'], '@maintainer')
            self.assertEqual(assigned['warnings'], [])
            self.assertNotEqual(row['notification_digest'], assigned['notification_digest'])

    def test_fourteen_day_boundary_and_no_change_review_are_independent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = repository(root)
            updated = maintenance.utc(maintenance.last_update(root, skill))
            now = (updated + timedelta(days=14)).isoformat()
            state = {'sources': {'docs': {'status': 'ok', 'digest': 'a', 'baseline_digest': 'a', 'observed_at': now}}}
            earlier = maintenance.report(root, state, (updated + timedelta(days=13, hours=23)).isoformat())[0]
            self.assertNotIn('no update in 14 days', earlier['warnings'])
            row = maintenance.report(root, state, now)[0]
            self.assertIn('no update in 14 days', row['warnings'])
            self.assertIn('review overdue', row['warnings'])
            maintenance.record_review(root, 'financial/example', state, 'Verified the documented contract', now)
            row = maintenance.report(root, state, now)[0]
            self.assertIn('unchanged, verified current', row['status'])
            self.assertEqual(row['update_age_days'], 14)
            self.assertNotIn('review overdue', row['warnings'])
            self.assertEqual(row['version'], '1.0.0')

    def test_version_only_commits_do_not_refresh_content_age(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = repository(root)
            updated = maintenance.last_update(root, skill)
            lifecycle.bump(root, 'financial/example', 'patch', 'Maintenance metadata')
            lifecycle.git(root, 'add', '.')
            later = (maintenance.utc(updated) + timedelta(minutes=1)).isoformat()
            with patch.dict(os.environ, {'GIT_COMMITTER_DATE': later}):
                lifecycle.git(root, 'commit', '-m', 'Only version and changelog')
            self.assertEqual(maintenance.last_update(root, skill), updated)

    def test_vendor_versions_and_initial_metadata_container_are_not_content(self):
        before = {'SKILL.md': b'---\nname: test\n---\n# Test\n'}
        after = {'SKILL.md': b'---\nname: test\nmetadata:\n  version: "1.0.0"\n---\n# Test\n'}
        self.assertEqual(lifecycle.substantive_content(before), lifecycle.substantive_content(after))
        first = {'SKILL.md': b'---\nname: test\nmetadata:\n  version: "1.0.0"\n  aisa:\n    version: 1.0.0\n---\n# Test\n'}
        second = {'SKILL.md': first['SKILL.md'].replace(b'1.0.0', b'1.0.1')}
        self.assertEqual(lifecycle.substantive_content(first), lifecycle.substantive_content(second))

    def test_upstream_change_remains_pending_across_successful_polls(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository(root)
            now = datetime.now(timezone.utc).isoformat()
            sources = lifecycle.read_json(root / 'maintenance/upstreams.json')
            with patch.object(maintenance, 'bounded_observe', return_value='first'):
                first = maintenance.monitor(sources, {}, now)
            maintenance.record_review(root, 'financial/example', first, 'Checked upstream', now)
            with patch.object(maintenance, 'bounded_observe', return_value='second'):
                second = maintenance.monitor(sources, first, now)
                third = maintenance.monitor(sources, second, now)
            self.assertEqual(third['sources']['docs']['previous_value'], 'first')
            self.assertEqual(maintenance.report(root, third, now)[0]['changed_upstreams'], ['docs'])
            maintenance.record_review(root, 'financial/example', third, 'Assessed the changed contract', now)
            self.assertEqual(maintenance.report(root, third, now)[0]['changed_upstreams'], [])

    def test_outage_preserves_last_good_evidence_and_is_not_currency(self):
        sources = {'docs': {'type': 'docs', 'url': 'https://example.com'}}
        now = datetime.now(timezone.utc).isoformat()
        with patch.object(maintenance, 'bounded_observe', return_value='first'):
            first = maintenance.monitor(sources, {}, now)
        with patch.object(maintenance, 'bounded_observe', side_effect=OSError('sensitive query token must not be logged')):
            second = maintenance.monitor(sources, first, now)
        self.assertEqual(second['sources']['docs']['digest'], first['sources']['docs']['digest'])
        self.assertEqual(second['sources']['docs']['status'], 'unavailable')
        self.assertNotIn('sensitive', json.dumps(second))

    def test_stale_or_failed_snapshots_cannot_be_verified(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository(root)
            now = datetime.now(timezone.utc)
            state = {'sources': {'docs': {'status': 'ok', 'digest': 'a', 'observed_at': (now - timedelta(days=2)).isoformat()}}}
            with self.assertRaisesRegex(ValueError, '24 hours'):
                maintenance.record_review(root, 'financial/example', state, 'Reviewed', now.isoformat())
            state['sources']['docs']['observed_at'] = now.isoformat()
            state['sources']['docs']['status'] = 'unavailable'
            with self.assertRaisesRegex(ValueError, 'successful snapshot'):
                maintenance.record_review(root, 'financial/example', state, 'Reviewed', now.isoformat())

    def test_notification_identity_does_not_change_just_because_age_increases(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = repository(root)
            updated = maintenance.utc(maintenance.last_update(root, skill))
            first = maintenance.report(root, {}, (updated + timedelta(days=14)).isoformat())[0]
            second = maintenance.report(root, {}, (updated + timedelta(days=15)).isoformat())[0]
            self.assertEqual(first['notification_digest'], second['notification_digest'])


class AdapterTests(unittest.TestCase):
    def test_openapi_tracks_selected_paths_and_transitive_references(self):
        specification = {'paths': {'/financial/prices': {'get': {'responses': {'200': {'$ref': '#/components/schemas/Prices'}}}}, '/unrelated': {}},
            'components': {'schemas': {'Prices': {'type': 'array', 'items': {'$ref': '#/components/schemas/Price'}}, 'Price': {'type': 'number'}, 'Unrelated': {'type': 'string'}}}}
        source = {'type': 'openapi', 'url': 'https://example.com/spec.json', 'paths': ['financial']}
        with patch.object(maintenance, 'request', return_value=(json.dumps(specification), {})):
            first = maintenance.observe(source)
        specification['paths']['/unrelated'] = {'post': {}}
        specification['components']['schemas']['Unrelated'] = {'type': 'object'}
        with patch.object(maintenance, 'request', return_value=(json.dumps(specification), {})):
            self.assertEqual(first, maintenance.observe(source))
        specification['components']['schemas']['Price'] = {'type': 'string'}
        with patch.object(maintenance, 'request', return_value=(json.dumps(specification), {})):
            self.assertNotEqual(first, maintenance.observe(source))

    def test_mcp_discovery_handles_sessions_and_pagination_without_execution(self):
        calls = []
        def rpc(url, body=None, headers=None):
            calls.append((body, headers.copy()))
            if body['method'] == 'initialize':
                return json.dumps({'id': 1, 'result': {'protocolVersion': '2025-11-25'}}), {'Mcp-Session-Id': 'session'}
            if body['method'] == 'notifications/initialized':
                return '', {}
            result = {'tools': [{'name': 'b', 'inputSchema': {'type': 'object'}}], 'nextCursor': 'next'} if body['id'] == 2 else {'tools': [{'name': 'a', 'inputSchema': {'type': 'object'}}]}
            return 'event: message\ndata: ' + json.dumps({'id': body['id'], 'result': result}) + '\n\n', {}
        with patch.object(maintenance, 'request', side_effect=rpc), patch.dict(os.environ, {'AISA_MONITOR_MCP_TOKEN': 'test-only-token'}):
            value = maintenance.observe({'type': 'mcp', 'url': 'https://example.com/mcp'})
        self.assertEqual([t['name'] for t in value['tools']], ['a', 'b'])
        self.assertEqual(calls[-1][0]['params'], {'cursor': 'next'})
        self.assertEqual(calls[-1][1]['Mcp-Session-Id'], 'session')
        self.assertNotIn('tools/call', [c[0]['method'] for c in calls])

    def test_docs_whitespace_is_normalized_and_html_is_rejected(self):
        with patch.object(maintenance, 'request', return_value=('# Docs  \r\n\r\nText\r\n', {})):
            self.assertEqual(maintenance.observe({'type': 'docs', 'url': 'https://example.com/docs'}), '# Docs\n\nText')
        with patch.object(maintenance, 'request', return_value=('<!doctype html><html>Navigation</html>', {})):
            with self.assertRaisesRegex(ValueError, 'received HTML'):
                maintenance.observe({'type': 'docs', 'url': 'https://example.com/docs'})

    def test_unchanged_issue_is_not_edited_or_commented(self):
        row = {'skill': 'financial/example', 'warnings': ['review overdue'], 'notification_digest': 'same'}
        issue = {'title': 'Skill maintenance: financial/example', 'body': '<!-- skill-maintenance:same -->', 'state': 'OPEN', 'number': 1}
        with patch.object(maintenance.subprocess, 'check_output', return_value=json.dumps([issue])), patch.object(maintenance.subprocess, 'run') as run:
            maintenance.notify([row], lifecycle.PUBLISH_REPOSITORY)
            run.assert_not_called()

    def test_source_deadline_is_enforced_and_failure_is_sanitized(self):
        with patch.object(maintenance.subprocess, 'run', side_effect=subprocess.TimeoutExpired([], 90)) as run:
            snapshot = maintenance.monitor({'docs': {'type': 'docs', 'url': 'https://example.com'}}, {}, '2026-10-10T01:00:00+00:00')
            self.assertEqual(snapshot['sources']['docs']['status'], 'unavailable')
            self.assertEqual(snapshot['sources']['docs']['error'], 'TimeoutExpired')
            self.assertEqual(run.call_args.kwargs['timeout'], 90)


if __name__ == '__main__':
    unittest.main()
