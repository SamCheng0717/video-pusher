import os, sys, subprocess

def test_script_requires_title():
    r = subprocess.run(
        [sys.executable, 'skills/vp-publish-ins/publish_ins.py', '--group', 'A组'],
        capture_output=True, text=True,
        cwd=os.path.join(os.path.dirname(__file__), '..')
    )
    assert r.returncode != 0

def test_profile_base_three_levels_up():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'skills', 'vp-publish-ins'))
    import publish_ins
    assert 'skills' not in publish_ins.PROFILE_BASE
    assert publish_ins.PROFILE_BASE.endswith('profile')
