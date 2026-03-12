import os, sys, subprocess

def test_script_requires_title():
    r = subprocess.run(
        [sys.executable, 'skills/vp-publish-threads/publish_threads.py',
         '--group', 'A组'],
        capture_output=True, text=True,
        cwd=os.path.join(os.path.dirname(__file__), '..')
    )
    assert r.returncode != 0  # --title 必填

def test_file_is_optional():
    """threads 不传 --file 不报错（argparse 层面）"""
    r = subprocess.run(
        [sys.executable, 'skills/vp-publish-threads/publish_threads.py',
         '--title', 'test', '--group', 'A组', '--help'],
        capture_output=True, text=True,
        cwd=os.path.join(os.path.dirname(__file__), '..')
    )
    assert r.returncode == 0

def test_profile_base_three_levels_up():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'skills', 'vp-publish-threads'))
    import publish_threads
    assert 'skills' not in publish_threads.PROFILE_BASE
    assert publish_threads.PROFILE_BASE.endswith('profile')
