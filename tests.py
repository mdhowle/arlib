import os
import nose
import shutil
import logging
import tempfile

import arlib

logging.getLogger("arlib").setLevel(logging.DEBUG)

temp_dir = None

def setup():
    global temp_dir
    temp_dir = tempfile.mkdtemp()

def teardown():
    global temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

@nose.with_setup(setup, teardown)
def test_loading_bsd_archive():
    global temp_dir

    arc = arlib.Archive()
    arc.load("test_subjects/bsd1.a")
    assert arc.format == arlib.BSD
    assert arc.symbols is not None
    assert len(arc) == 5

    filenames = sorted([m.filename for m in arc])
    expected = ["alpha.o", "another_long_file_name.o", "test.o", "this_is_a_long_file_name.o", "zeta.o"]
    assert expected == filenames
    assert arc["test.o"].mode == 0o100644

    arc.extract_all(temp_dir)
    for f in expected:
        s = os.stat(os.path.join(temp_dir, f))
        assert s.st_mode == arc[f].mode
        assert s.st_size == arc[f].filesize
        assert s.st_mtime == arc[f].date

@nose.with_setup(setup, teardown)
def test_loading_gnu_archive():
    global temp_dir

    arc = arlib.Archive()
    arc.load("test_subjects/gnu1.a")
    assert arc.format == arlib.GNU
    assert arc.symbols is not None
    assert arc.strings is not None
    assert len(arc) == 5

    filenames = sorted([m.filename for m in arc])
    expected = ["alpha.o", "another_long_file_name.o", "test.o", "this_is_a_long_file_name.o", "zeta.o"]
    assert expected == filenames
    assert arc["test.o"].mode == 0o100644

    arc.extract_all(temp_dir)
    for f in expected:
        s = os.stat(os.path.join(temp_dir, f))
        assert s.st_mode == arc[f].mode
        assert s.st_size == arc[f].filesize
        assert s.st_mtime == arc[f].date

@nose.with_setup(setup, teardown)
def test_creating_bsd_archive():
    global temp_dir

    c = arlib.Archive(format=arlib.BSD)
    c.add("test_subjects/source/alpha.c")
    c.add("test_subjects/source/another_long_file_name.c")
    c.add("test_subjects/source/test.c")
    c.add("test_subjects/source/this_is_a_long_file_name.c")
    c.add("test_subjects/source/zeta.c")
    c.save(os.path.join(temp_dir, "bsd.a"))
