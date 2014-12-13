import os
import shutil
import logging

import arlib

logging.getLogger("arlib").setLevel(logging.DEBUG)

def test_loading_bsd_archive():
    shutil.rmtree("bsd1", ignore_errors=True)

    arc = arlib.Archive()
    arc.load("test_subjects/bsd1.a")
    assert arc.format == arlib.BSD
    assert arc.symbols is not None
    assert len(arc) == 5

    filenames = sorted([m.filename for m in arc])
    expected = ["alpha.o", "another_long_file_name.o", "test.o", "this_is_a_long_file_name.o", "zeta.o"]
    assert expected == filenames
    assert arc["test.o"].mode == 0o100644

    arc.extract_all("bsd1")
    for f in expected:
        s = os.stat(os.path.join("bsd1", f))
        assert s.st_mode == arc[f].mode
        assert s.st_size == arc[f].filesize
        assert s.st_mtime == arc[f].date

def test_loading_gnu_archive():
    shutil.rmtree("gnu1", ignore_errors=True)

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

    arc.extract_all("gnu1")
    for f in expected:
        s = os.stat(os.path.join("gnu1", f))
        assert s.st_mode == arc[f].mode
        assert s.st_size == arc[f].filesize
        assert s.st_mtime == arc[f].date

# print "===="

# longpath1 = "/tmp/this_is_a_file_with_a_long_name.txt"
# longpath2 = "/tmp/this_is_a_file_with_a_long_name_also.txt"
# text = """Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed
# consectetur suscipit porta. Sed et fermentum mi. Maecenas sed nibh ac arcu
# condimentum finibus pellentesque sit amet magna. Proin porta ac eros quis
# feugiat. Nullam eu nibh bibendum, condimentum metus in, accumsan risus.
# Vivamus est massa, euismod sit amet consectetur ac, mattis in elit. Duis nisi
# velit, pulvinar in tempus quis, vehicula eu nibh. Mauris posuere vehicula
# gravida. Sed et justo ipsum. Integer et finibus orci. Vestibulum vitae dapibus
# sem."""
# open(longpath1, "wb").write(text)
# open(longpath2, "wb").write(text.upper())

# c = arlib.Archive(format=arlib.BSD)
# c.add_member(".gitignore")
# c.add_member("LICENSE.txt")
# c.add_member(longpath1)
# c.add_member("README.md")
# c.add_member(longpath2)
# c.save("/tmp/bsd.a")

# print "===="

# c = arlib.Archive(format=arlib.GNU)
# c.add_member(".gitignore")
# c.add_member("LICENSE.txt")
# c.add_member(longpath1)
# c.add_member("README.md")
# c.add_member(longpath2)
# c.save("/tmp/gnu.a")
