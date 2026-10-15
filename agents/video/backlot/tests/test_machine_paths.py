from backlot.config import load_studio, studio_path


def test_machine_projects_root(monkeypatch, tmp_path):
    root = tmp_path / 'Projects with spaces'
    monkeypatch.setenv('DOTFILES_PROJECTS_ROOT', str(root))
    monkeypatch.delenv('BACKLOT_STUDIO', raising=False)
    expected = root / 'video/backlot/studio.yaml'
    assert studio_path() == expected
    expected.parent.mkdir(parents=True)
    expected.write_text('vault: ~/projects/obsidian/Backlot\nprojects_root: ~/projects/video/backlot\n')
    studio = load_studio()
    assert studio.vault == root / 'obsidian/Backlot'
    assert studio.projects_root == root / 'video/backlot'


def test_explicit_studio_paths_are_preserved(monkeypatch, tmp_path):
    monkeypatch.setenv('DOTFILES_PROJECTS_ROOT', '/another/root')
    config = tmp_path / 'studio.yaml'
    config.write_text('vault: /custom/vault\nprojects_root: /custom/projects\n')
    assert str(load_studio(config).vault) == '/custom/vault'
