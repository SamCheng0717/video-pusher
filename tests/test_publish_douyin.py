import os, sys, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'skills', 'vp-publish-douyin'))

def test_script_requires_file():
    r = subprocess.run(
        [sys.executable, 'skills/vp-publish-douyin/publish_douyin.py',
         '--title', 'test', '--description', 'x', '--group', 'A组'],
        capture_output=True, text=True,
        cwd=os.path.join(os.path.dirname(__file__), '..')
    )
    assert r.returncode != 0  # --file 是必填项

def test_script_requires_title():
    r = subprocess.run(
        [sys.executable, 'skills/vp-publish-douyin/publish_douyin.py',
         '--file', '/tmp/x.mp4', '--group', 'A组'],
        capture_output=True, text=True,
        cwd=os.path.join(os.path.dirname(__file__), '..')
    )
    assert r.returncode != 0  # --title 是必填项

def test_profile_base_three_levels_up():
    import publish_douyin
    assert 'skills' not in publish_douyin.PROFILE_BASE
    assert publish_douyin.PROFILE_BASE.endswith('profile')
