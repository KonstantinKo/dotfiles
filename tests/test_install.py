"""Installer contracts exercised in disposable homes, without network access."""
import os
from pathlib import Path
import subprocess
import tempfile
import shutil
import unittest

ROOT = Path(__file__).resolve().parents[1]


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.env = dict(os.environ, HOME=str(self.home))
        for key in list(self.env):
            if key.startswith('DOTFILES_'):
                self.env.pop(key)

    def install(self, *args):
        return subprocess.run(['bash', str(ROOT / 'install.sh'), '--offline', *args],
                              env=self.env, capture_output=True, text=True, check=True)

    def test_option_precedence_and_empty_environment_exclusion(self):
        self.install('--workspaces', 'personal')
        self.env.update(DOTFILES_WORKSPACES='games', DOTFILES_EXCLUDE_SKILLS='game-engines',
                        DOTFILES_PROJECTS_ROOT=str(self.home / 'custom-projects'))
        self.install()
        skills = self.home / '.codex-games/skills'
        self.assertTrue((skills / 'game-loop').is_symlink())
        self.assertFalse((skills / 'game-engines').exists())
        self.env.update(DOTFILES_WORKSPACES='personal', DOTFILES_EXCLUDE_SKILLS='')
        self.install('--workspaces', 'games,video')
        self.assertTrue((skills / 'game-engines').is_symlink())
        self.assertTrue((self.home / 'custom-projects/video/.mcp.json').is_symlink())
        self.assertFalse((self.home / 'projects/video').exists())
        self.env.pop('DOTFILES_WORKSPACES')
        self.env.pop('DOTFILES_EXCLUDE_SKILLS')
        self.env.pop('DOTFILES_PROJECTS_ROOT')
        self.install()
        self.assertTrue((skills / 'game-engines').is_symlink())
        self.assertTrue((self.home / 'custom-projects/video/.mcp.json').is_symlink())

    def test_private_profile_preserves_shell_auth_and_persists_choices(self):
        bashrc = self.home / '.bashrc'
        bashrc.write_text('# Omarchy setup\n')
        auth = self.home / '.codex-games/auth.json'
        auth.parent.mkdir()
        auth.write_text('private auth sentinel')
        projects = self.home / 'Projects with spaces'
        self.install('--workspaces', 'games,creative,video,personal', '--projects-root', str(projects))
        for name in ['.claude', '.codex', '.claude-di', '.codex-di', '.cursor']:
            self.assertFalse((self.home / name).exists(), name)
        self.assertFalse((self.home / '.config/dotfiles/git.local').exists())
        self.assertTrue(bashrc.read_text().startswith('# Omarchy setup\n'))
        self.assertEqual(auth.read_text(), 'private auth sentinel')
        self.assertTrue((projects / 'video/.mcp.json').is_symlink())
        self.assertFalse((projects / 'platform').exists())
        work_links = [p for p in self.home.rglob('*') if p.is_symlink() and '/agents/work/' in str(p.readlink())]
        # Shared statusline is safe, contains no company services or credentials.
        self.assertEqual(work_links, [])
        self.install()
        self.assertEqual(bashrc.read_text().count('dotfiles/shell.sh'), 2)
        self.assertFalse((self.home / '.dotfiles-backup').exists())
        config = self.home / '.codex-games/config.toml'
        config.write_text(config.read_text() + '\n# local edit\n')
        self.install()
        self.assertIn('# local edit', config.read_text())
        self.assertEqual(auth.read_text(), 'private auth sentinel')

    def test_skill_selection_updates_only_managed_links(self):
        self.install('--workspaces', 'games')
        skills = self.home / '.codex-games/skills'
        custom = skills / 'my-local-skill'
        custom.mkdir()
        (custom / 'SKILL.md').write_text('keep me')
        self.assertTrue((skills / 'game-engines').is_symlink())
        self.install('--exclude-skills', 'game-engines')
        self.assertFalse((skills / 'game-engines').exists())
        self.assertTrue((custom / 'SKILL.md').exists())
        self.assertTrue((skills / 'game-loop').is_symlink())

    def test_backup_preserves_existing_dangling_symlink(self):
        source = self.home / 'config'
        source.write_text('keep current config')
        backup_root = self.home / 'backups'
        backup_root.mkdir()
        first = backup_root / 'config'
        first.symlink_to(self.home / 'missing-old-target')
        script = (ROOT / 'install.sh').read_text()
        backup_function = script[script.index('backup() {'):script.index('safe_symlink() {')]
        runner = self.home / 'backup-test.sh'
        runner.write_text('set -euo pipefail\n' + backup_function + '\nbackup "$HOME/config"\n')
        subprocess.run(['/bin/bash', str(runner)], env=dict(self.env, BACKUP_ROOT=str(backup_root)),
                       capture_output=True, text=True, check=True)
        self.assertTrue(first.is_symlink())
        self.assertEqual(first.readlink(), self.home / 'missing-old-target')
        self.assertEqual((backup_root / 'config.1').read_text(), 'keep current config')

    def test_repeated_skill_backup_retains_versions_outside_repository(self):
        # Use a repository copy so a regression cannot mutate the real checkout.
        fixture = self.home / 'dotfiles'
        shutil.copytree(ROOT, fixture, ignore=shutil.ignore_patterns(
            '.git', '.venv', '__pycache__', '.pytest_cache'))
        skill = 'html-communication'
        shared = fixture / 'agents/shared/skills' / skill
        work = fixture / 'agents/work/skills' / skill
        self.assertTrue(shared.is_dir())
        self.assertTrue(work.is_dir())
        target = self.home / '.claude-di/skills' / skill
        target.parent.mkdir(parents=True)
        target.symlink_to(work)
        command = ['/bin/bash', str(fixture / 'install.sh'), '--offline', '--workspaces',
                   'work,games,creative,video,personal']
        for _ in range(2):
            subprocess.run(command, env=self.env, capture_output=True, text=True, check=True)
            self.assertEqual(target.readlink(), work)
            self.assertFalse((work / skill).is_symlink())
            self.assertFalse((shared / skill).is_symlink())
            self.assertTrue((self.home / '.config/dotfiles/links.tsv').is_file())
        backups = list((self.home / '.dotfiles-backup').glob('*/.claude-di/skills/' + skill + '*'))
        self.assertGreaterEqual(len(backups), 4)
        self.assertEqual({path.readlink() for path in backups}, {work, shared})

    def test_work_profile_and_backups(self):
        config = self.home / '.gitconfig'
        config.write_text('[user]\nname = Existing\n')
        self.install('--workspaces', 'work')
        self.assertTrue((self.home / '.claude-di/AGENTS.md').is_symlink())
        self.assertFalse((self.home / '.codex-games').exists())
        self.assertTrue((self.home / '.codex-di/config.toml').exists())
        self.assertTrue(list((self.home / '.dotfiles-backup').glob('*/.gitconfig')))
        self.assertIn('doinstruct.com', (self.home / '.config/dotfiles/git.local').read_text())

    def test_personal_only_and_shell_functions(self):
        self.install('--workspaces', 'personal')
        self.assertFalse((self.home / '.codex-games').exists())
        for shell in ['bash', 'zsh']:
            if not shutil.which(shell):
                continue
            result = subprocess.run([shell, '-c', '. "$HOME/.config/dotfiles/shell.sh"; codg'], env=self.env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn('not installed', result.stderr)

    def test_stock_bash_workspace_without_agent_homes(self):
        for workspace in ['personal', 'video', 'creative']:
            with self.subTest(workspace=workspace), tempfile.TemporaryDirectory() as home:
                env = dict(self.env, HOME=home)
                subprocess.run(['/bin/bash', str(ROOT / 'install.sh'), '--offline',
                                '--workspaces', workspace], env=env, capture_output=True,
                               text=True, check=True)
                home = Path(home)
                manifest = home / '.config/dotfiles/links.tsv'
                self.assertTrue(manifest.is_file())
                self.assertIn('shell.sh', manifest.read_text())
                if workspace == 'personal':
                    self.assertTrue((home / 'projects/obsidian/spse/AGENTS.md').is_symlink())
                if workspace == 'video':
                    self.assertTrue((home / 'projects/video/.mcp.json').is_symlink())

    def test_installer_failure_preserves_exit_status(self):
        tools = self.home / 'tools'
        tools.mkdir()
        ln = tools / 'ln'
        ln.write_text('#!/bin/sh\nexit 23\n')
        ln.chmod(0o755)
        env = dict(self.env, PATH=str(tools) + ':' + os.environ['PATH'])
        result = subprocess.run(['/bin/bash', str(ROOT / 'install.sh'), '--offline',
                                 '--workspaces', 'personal'], env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 23)
        self.assertFalse((self.home / '.config/dotfiles/links.tsv').exists())

    def test_posix_profile_reaches_end(self):
        shell = shutil.which('dash')
        if not shell:
            self.skipTest('dash is not installed')
        self.install('--workspaces', 'personal')
        env = dict(self.env)
        env.pop('BASH_VERSION', None)
        env.pop('ZSH_VERSION', None)
        result = subprocess.run([shell, '-c', '. "$HOME/.profile"; echo reached'],
                                env=env, capture_output=True, text=True, check=True)
        self.assertEqual(result.stdout.strip(), 'reached')
        result = subprocess.run([shell, '-c', '. "$HOME/.config/dotfiles/shell.sh"; echo reached'],
                                env=env, capture_output=True, text=True, check=True)
        self.assertEqual(result.stdout.strip(), 'reached')

    def test_linux_godot_runtime(self):
        tools = self.home / 'tools'
        tools.mkdir()
        for name, body in {
            'uname': 'echo Linux',
            'timeout': 'shift; exec "$@"',
            'godot': 'printf "%s\\n" "$@"',
        }.items():
            tool = tools / name
            tool.write_text('#!/bin/sh\n' + body + '\n')
            tool.chmod(0o755)
        env = dict(self.env, PATH=str(tools) + ':' + os.environ['PATH'])
        result = subprocess.run([str(ROOT / 'agents/games/skills/godot-quiet/godot-quiet'),
                                 '--path', '/tmp/project with spaces', '--quit'],
                                env=env, capture_output=True, text=True, check=True)
        self.assertEqual(result.stdout.splitlines(),
                         ['--headless', '--audio-driver', 'Dummy', '--path', '/tmp/project with spaces', '--quit'])

    def test_fal_key_file_permissions(self):
        key = self.home / 'key'
        key.write_text('test-only-placeholder')
        env = dict(self.env, FAL_KEY_FILE=str(key))
        env.pop('FAL_KEY', None)
        key.chmod(0o600)
        cmd = [str(ROOT / 'bin/dotfiles-fal-key')]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        self.assertEqual(result.stdout, 'test-only-placeholder')
        key.chmod(0o644)
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 78)
        self.assertEqual(result.stdout, '')


if __name__ == '__main__':
    unittest.main()
