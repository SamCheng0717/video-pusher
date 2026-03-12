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
