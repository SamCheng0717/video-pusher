# tests/test_vp_accounts.py
import os, sys, json, tempfile, pytest

# 让测试能 import vp_accounts
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'skills', 'vp-accounts'))
import vp_accounts

def test_profile_base_is_three_levels_up():
    """PROFILE_BASE 必须指向 video-pusher/profile/，即脚本上三级"""
    base = vp_accounts.PROFILE_BASE
    assert base.endswith('profile')
    assert 'skills' not in base  # 不能落在 skills/ 内

def test_load_accounts_returns_empty_when_file_missing(tmp_path):
    accounts = vp_accounts.load_accounts(tmp_path / 'accounts.json')
    assert accounts == []

def test_save_and_load_accounts(tmp_path):
    path = tmp_path / 'accounts.json'
    data = [{'name': 'A组', 'platforms': {'douyin': 'douyin/group_0'}}]
    vp_accounts.save_accounts(path, data)
    loaded = vp_accounts.load_accounts(path)
    assert loaded == data

def test_get_profile_subpath():
    accounts = [
        {'name': 'A组', 'platforms': {}},
        {'name': 'B组', 'platforms': {}},
    ]
    assert vp_accounts.get_profile_subpath(accounts, 'A组', 'douyin') == 'douyin/group_0'
    assert vp_accounts.get_profile_subpath(accounts, 'B组', 'douyin') == 'douyin/group_1'

def test_get_profile_subpath_raises_when_group_not_found():
    with pytest.raises(ValueError, match='不存在'):
        vp_accounts.get_profile_subpath([], '不存在组', 'douyin')

def test_format_tags():
    assert vp_accounts.format_tags('医美 玻尿酸') == '#医美 #玻尿酸'
    assert vp_accounts.format_tags('#医美 #玻尿酸') == '#医美 #玻尿酸'   # 已有 # 不重复
    assert vp_accounts.format_tags('') == ''
    assert vp_accounts.format_tags(None) == ''


# ── CLI 命令测试 ────────────────────────────────────────────

def test_cli_list_empty(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(vp_accounts, 'ACCOUNTS_FILE', str(tmp_path / 'accounts.json'))
    vp_accounts.cmd_list()
    captured = capsys.readouterr()
    assert json.loads(captured.out) == []

def test_cli_add_and_list(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(vp_accounts, 'ACCOUNTS_FILE', str(tmp_path / 'accounts.json'))
    vp_accounts.cmd_add('A组')
    vp_accounts.cmd_list()
    captured = capsys.readouterr()
    # cmd_add 的输出 + cmd_list 的输出，提取 JSON 对象（以 [ 开头）
    lines = captured.out.strip().split('\n')
    # 找到 JSON 数组的起始行（以 [ 开头）
    json_start = None
    for i, line in enumerate(lines):
        if line.startswith('['):
            json_start = i
            break
    assert json_start is not None, f"No JSON found in output: {captured.out}"
    # 从该行开始，合并所有行直到找到对应的结束 ]
    json_str = '\n'.join(lines[json_start:])
    data = json.loads(json_str)
    assert data[0]['name'] == 'A组'
    assert data[0]['platforms']['douyin'] == False

def test_cli_add_duplicate_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(vp_accounts, 'ACCOUNTS_FILE', str(tmp_path / 'accounts.json'))
    vp_accounts.cmd_add('A组')
    with pytest.raises(SystemExit) as exc:
        vp_accounts.cmd_add('A组')
    assert exc.value.code == 1

def test_cli_delete(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(vp_accounts, 'ACCOUNTS_FILE', str(tmp_path / 'accounts.json'))
    vp_accounts.cmd_add('A组')
    vp_accounts.cmd_delete('A组')
    vp_accounts.cmd_list()
    captured = capsys.readouterr()
    lines = captured.out.strip().split('\n')
    json_start = None
    for i, line in enumerate(lines):
        if line.startswith('['):
            json_start = i
            break
    json_str = '\n'.join(lines[json_start:])
    assert json.loads(json_str) == []

def test_cli_status_not_logged_in(tmp_path, monkeypatch):
    monkeypatch.setattr(vp_accounts, 'ACCOUNTS_FILE', str(tmp_path / 'accounts.json'))
    vp_accounts.cmd_add('A组')
    with pytest.raises(SystemExit) as exc:
        vp_accounts.cmd_status('A组', 'douyin')
    assert exc.value.code == 1

def test_cli_status_logged_in(tmp_path, monkeypatch):
    monkeypatch.setattr(vp_accounts, 'ACCOUNTS_FILE', str(tmp_path / 'accounts.json'))
    monkeypatch.setattr(vp_accounts, 'PROFILE_BASE', str(tmp_path / 'profile'))
    data = [{'name': 'A组', 'platforms': {'douyin': 'douyin/group_0'}}]
    vp_accounts.save_accounts(str(tmp_path / 'accounts.json'), data)
    os.makedirs(str(tmp_path / 'profile' / 'douyin' / 'group_0'), exist_ok=True)
    with pytest.raises(SystemExit) as exc:
        vp_accounts.cmd_status('A组', 'douyin')
    assert exc.value.code == 0
