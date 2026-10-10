"""Integration check: install a locked TS compiler and test a standalone bundle."""
from pathlib import Path
import shutil
import tempfile

from test_skill_lifecycle import repository, lifecycle


def main() -> None:
    fixture = Path(__file__).parent / 'fixtures/typescript-skill'
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        skill = repository(root)
        shutil.copytree(fixture, skill, dirs_exist_ok=True)
        manifest = lifecycle.read_json(skill / 'skill.json')
        manifest.update(languages=['typescript', 'javascript'], runtime={'node': '22'}, entrypoints=['dist/client.js'],
                        checks={'typecheck': [['npm', 'run', 'typecheck']], 'build': [['npm', 'run', 'build']], 'test': [['npm', 'test']]})
        lifecycle.write_json(skill / 'skill.json', manifest)
        issues = lifecycle.validate(root)
        if issues:
            raise AssertionError(issues)
        lifecycle.run_checks(root)
        print('Locked TypeScript build and exported JavaScript contract passed')


if __name__ == '__main__':
    main()
