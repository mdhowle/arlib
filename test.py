import logging

import arlib

logging.getLogger("arlib").setLevel(logging.DEBUG)

a = arlib.Archive()
a.load("/tmp/libpng.a")

print "===="

b = arlib.Archive()
b.load("/tmp/libresolv.a")
