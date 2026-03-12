# tests/test_publish_xhs.py
import os, sys, subprocess

def test_script_requires_file():
    r = subprocess.run(
        [sys.executable, 'skills/vp-publish-xhs/publish_xhs.py',
         '--title', 'test', '--group', 'A组'],
        capture_output=True, text=True,
        cwd=os.path.join(os.path.dirname(__file__), '..')
    )
    assert r.returncode != 0

def test_profile_base_three_levels_up():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'skills', 'vp-publish-xhs'))
    import publish_xhs
    assert 'skills' not in publish_xhs.PROFILE_BASE
    assert publish_xhs.PROFILE_BASE.endswith('profile')
