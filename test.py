import logging

import arlib

logging.getLogger("arlib").setLevel(logging.DEBUG)

a = arlib.Archive()
a.load("/tmp/libpng.a")

print "===="

b = arlib.Archive()
b.load("/tmp/libresolv.a")

print "===="

longpath1 = "/tmp/this_is_a_file_with_a_long_name.txt"
longpath2 = "/tmp/this_is_a_file_with_a_long_name_also.txt"
text = """Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed
consectetur suscipit porta. Sed et fermentum mi. Maecenas sed nibh ac arcu
condimentum finibus pellentesque sit amet magna. Proin porta ac eros quis
feugiat. Nullam eu nibh bibendum, condimentum metus in, accumsan risus.
Vivamus est massa, euismod sit amet consectetur ac, mattis in elit. Duis nisi
velit, pulvinar in tempus quis, vehicula eu nibh. Mauris posuere vehicula
gravida. Sed et justo ipsum. Integer et finibus orci. Vestibulum vitae dapibus
sem."""
open(longpath1, "wb").write(text)
open(longpath2, "wb").write(text.upper())

c = arlib.Archive(format=arlib.BSD)
c.add_member(".gitignore")
c.add_member("LICENSE.txt")
c.add_member(longpath1)
c.add_member("README.md")
c.add_member(longpath2)
c.save("/tmp/bsd.a")

print "===="

c = arlib.Archive(format=arlib.GNU)
c.add_member(".gitignore")
c.add_member("LICENSE.txt")
c.add_member(longpath1)
c.add_member("README.md")
c.add_member(longpath2)
c.save("/tmp/gnu.a")
