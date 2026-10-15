"""GitHub credentials use gh even when the system installs another helper."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class GitConfigTests(unittest.TestCase):
    def test_gh_resets_inherited_helpers(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            tools = home / 'tools'
            tools.mkdir()
            marker = home / 'inherited-helper-called'
            inherited = tools / 'inherited'
            inherited.write_text('#!/bin/sh\ntouch "$HOME/inherited-helper-called"\n'
                                 'printf "username=company\\npassword=test-placeholder\\n"\n')
            inherited.chmod(0o755)
            gh = tools / 'gh'
            gh.write_text('#!/bin/sh\nprintf "username=personal\\npassword=test-placeholder\\n"\n')
            gh.chmod(0o755)
            system = home / 'system.gitconfig'
            system.write_text('[credential]\nhelper = ' + str(inherited) + '\n')
            env = dict(os.environ, HOME=tmp, PATH=str(tools) + ':' + os.environ['PATH'],
                       GIT_CONFIG_SYSTEM=str(system), GIT_CONFIG_GLOBAL=str(ROOT / '.gitconfig'),
                       GIT_CONFIG_NOSYSTEM='0', GIT_TERMINAL_PROMPT='0')
            for host in ['github.com', 'gist.github.com']:
                with self.subTest(host=host):
                    result = subprocess.run(['git', 'credential', 'fill'], env=env,
                                            input='protocol=https\nhost=' + host + '\n\n',
                                            capture_output=True, text=True, check=True)
                    self.assertIn('username=personal', result.stdout)
                    self.assertFalse(marker.exists())
