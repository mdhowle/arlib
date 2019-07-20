import logging
import os
import shutil
import tempfile
import unittest

import arlib

logging.getLogger("arlib").setLevel(logging.DEBUG)

class ArLibTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        self.temp_dir = None

    def test_loading_bsd_archive(self):
        arc = arlib.Archive()
        arc.load("test_subjects/bsd1.a")
        self.assertEqual(arc.format, arlib.BSD)
        self.assertNotEqual(arc.symbols, None)
        self.assertEqual(len(arc), 5)

        filenames = sorted([m.filename for m in arc])
        expected = ["alpha.o", "another_long_file_name.o", "test.o", "this_is_a_long_file_name.o", "zeta.o"]
        self.assertEqual(expected, filenames)
        self.assertEqual(arc["test.o"].mode, 0o100644)

        arc.extract_all(self.temp_dir)
        for f in expected:
            s = os.stat(os.path.join(self.temp_dir, f))
            self.assertEqual(s.st_mode, arc[f].mode)
            self.assertEqual(s.st_size, arc[f].filesize)
            self.assertEqual(s.st_mtime, arc[f].date) 

    def test_loading_gnu_archive(self):
        arc = arlib.Archive()
        arc.load("test_subjects/gnu1.a")
        self.assertEqual(arc.format, arlib.GNU)
        self.assertNotEqual(arc.symbols, None)
        self.assertNotEqual(arc.strings, None)
        self.assertEqual(len(arc), 5)

        filenames = sorted([m.filename for m in arc])
        expected = ["alpha.o", "another_long_file_name.o", "test.o", "this_is_a_long_file_name.o", "zeta.o"]
        self.assertEqual(expected, filenames)
        self.assertEqual(arc["test.o"].mode,  0o100644)

        arc.extract_all(self.temp_dir)
        for f in expected:
            s = os.stat(os.path.join(self.temp_dir, f))
            self.assertEqual(s.st_mode, arc[f].mode)
            self.assertEqual(s.st_size, arc[f].filesize)
            self.assertEqual(s.st_mtime, arc[f].date)

    def test_loading_deb_archive(self):
        arc = arlib.Archive()
        arc.load("test_subjects/test.deb")
        self.assertEqual(arc.format, arlib.DEB)
        self.assertEqual(arc.symbols, None)
        self.assertEqual(len(arc), 3)

        filenames = [m.filename for m in arc]
        expected = ["debian-binary", "control.tar.xz", "data.tar.xz"]
        self.assertEqual(expected, filenames)
        self.assertEqual(arc["debian-binary"].mode, 0o100644)

        arc.extract_all(self.temp_dir)
        for f in expected:
            s = os.stat(os.path.join(self.temp_dir, f))
            self.assertEqual(s.st_mode, arc[f].mode)
            self.assertEqual(s.st_size, arc[f].filesize)
            self.assertEqual(s.st_mtime, arc[f].date)

    def test_creating_bsd_archive(self):
        c = arlib.Archive(format=arlib.BSD)
        c.add("test_subjects/source/alpha.c")
        c.add("test_subjects/source/another_long_file_name.c")
        c.add("test_subjects/source/test.c")
        c.add("test_subjects/source/this_is_a_long_file_name.c")
        c.add("test_subjects/source/zeta.c")
        c.save(os.path.join(self.temp_dir, "bsd.a"))

    def test_creating_deb_archive(self):
        c = arlib.Archive(format=arlib.DEB)

        # Place in incorrect order
        c.add("test_subjects/deb_source/control.tar.xz")
        c.add("test_subjects/deb_source/data.tar.xz")
        c.add("test_subjects/deb_source/debian-binary")
        c.save(os.path.join(self.temp_dir, "test.deb"))
        c.outstream.close()

        d = arlib.Archive(format=arlib.DEB)
        d.load(os.path.join(self.temp_dir, "test.deb"))

        filenames = [m.name for m in d.members]
        expected = ["debian-binary", "control.tar.xz", "data.tar.xz"]
        self.assertEqual(filenames, expected)


if __name__ == '__main__':
    unittest.main()
