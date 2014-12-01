# References:
#   https://www.freebsd.org/cgi/man.cgi?query=ar&sektion=5&apropos=0&manpath=FreeBSD+10.1-RELEASE
#   http://www.opensource.apple.com/source/cctools/cctools-795/include/mach-o/ranlib.h

import os
import re
import time
import struct
import shutil
import logging

BLOCKSIZE = 65535
WHITESPACERE = re.compile(r"[\s]")

logging.basicConfig()
log = logging.getLogger("arlib")
log.setLevel(logging.INFO)

class WrongMemberTypeException(Exception):
    pass

class InvalidArchiveException(Exception):
    pass

class ArchiveMember(object):
    GNU = 0
    BSD = 1

    format = None

    _header_format = struct.Struct("=16s12s6s6s8s10s2s")
    _header_fill = " "
    _header_tail = "`\n"

    def __init__(self, archive, path=None):
        self._name = None
        self._filename = None
        self._size = 0
        self._offset = None

        self.archive = archive
        if path:
            self.init_from_file(path)
        else:
            self.init_from_archive()

    def __repr__(self):
        return "<{}(filename={}, name={}, date={}, uid={}, gid={}, mode=0{:04o}, size={})>".format(
            self.__class__.__name__, self.filename, self.name, self.date, self.uid, self.gid, self.mode, self.size)

    @property
    def name(self):
        return self._name
    @name.setter
    def name(self, value):
        self._name = value

    @property
    def filename(self):
        return self._filename
    @filename.setter
    def filename(self, value):
        self._filename = value

    @property
    def size(self):
        return self._size
    @size.setter
    def size(self, value):
        self._size = value

    @property
    def filesize(self):
        return self.size
    @filesize.setter
    def filesize(self, value):
        self.size = value

    @property
    def offset(self):
        return self._offset
    @offset.setter
    def offset(self, value):
        self._offset = value

    def init_from_file(self, path):
        prop = os.stat(path)

        self.set_name_from_file(os.path.basename(path))
        self.sourcedir = os.path.dirname(path)
        self.date = int(prop.st_mtime)
        self.uid = prop.st_uid
        self.gid = prop.st_gid
        self.mode = prop.st_mode
        self.filesize = prop.st_size
        self.offset = None

    def init_from_archive(self):
        header = self.archive.instream.read(self._header_format.size)
        if len(header) < self._header_format.size:
            raise EOFError()
        nameinfo, date, uid, gid, mode, size, tail = self._header_format.unpack(header)
        log.debug("Read header values: %s, %s, %s, %s, %s, %s",
            nameinfo.strip(), date.strip(), uid.strip(), gid.strip(), mode.strip(), size.strip())
        assert tail == self._header_tail

        self.set_name_from_archive(nameinfo.strip())
        self.sourcedir = None
        self.date = int(date.strip())
        self.uid = int(uid.strip())
        self.gid = int(gid.strip())
        self.mode = int(mode.strip(), 8)
        self.size = int(size.strip())
        self.offset = self.archive.instream.tell()

    @classmethod
    def derived(cls):
        classes = []
        for c in cls.__subclasses__():
            classes.append(c)
            classes += c.derived()
        return set(classes)

    def set_name_from_file(self, filename):
        raise NotImplementedError("The method set_name_from_file() must be implemented in derived classes.")

    def set_name_from_archive(self, nameinfo):
        raise NotImplementedError("The method set_name_from_archive() must be implemented in derived classes.")

    def write_header(self):
        name = self.name.ljust(16)
        date = str(self.date).ljust(12)
        uid = str(self.uid).ljust(6)
        gid = str(self.gid).ljust(6)
        mode = str(self.mode).ljust(8)
        size = str(self.size).ljust(10)

        packed = self._header_format.pack(name, date, uid, gid, mode, size, self._header_tail)
        self.archive.outstream.write(packed)

    def extract(self, path):
        filepath = os.path.join(path, self.filename)
        if self.sourcedir is None:
            with open(filepath, "wb") as outfile:
                infile = self.archive.instream
                infile.seek(self.offset)
                remaining = self.filesize
                while remaining >= BLOCKSIZE:
                    buf = infile.read(BLOCKSIZE)
                    outfile.write(buf)
                    remaining -= BLOCKSIZE
                if remaining > 0:
                    buf = infile.read(remaining)
                    outfile.write(buf)
            os.chmod(filepath, self.mode)
            try:
                os.chown(filepath, self.uid, self.gid)
            except:
                pass
            os.utime(filepath, (time.time(), self.date))
        else:
            externalfile = os.path.join(self.sourcedir, self.filename)
            shutil.copy2(externalfile, filepath)

    def collect(self):
        outfile = self.archive.outstream
        newoffset = outfile.tell()
        infile = None
        if not self.sourcedir is None:
            infile = self.archive.instream
            infile.seek(self.offset)
        else:
            externalfile = os.path.join(self.sourcedir, self.filename)
            infile = open(externalfile, "rb")

        remaining = self.filesize
        while remaining >= BLOCKSIZE:
            buf = infile.read(BLOCKSIZE)
            outfile.write(buf)
            remaining -= BLOCKSIZE
        if remaining > 0:
            buf = infile.read(remaining)
            outfile.write(buf)
        self.offset = newoffset
        self.sourcedir = None

class GNUShortMember(ArchiveMember):
    format = ArchiveMember.GNU

    _name_terminal = "/"

    def set_name_from_file(self, filename):
        if len(filename) < 16 and not WHITESPACERE.search(filename):
            self.filename = filename
            self.name = filename + self._name_terminal
        else:
            raise WrongMemberTypeException("Not a short GNU archive member.")

    def set_name_from_archive(self, nameinfo):
        if len(nameinfo) > 1 and nameinfo.endswith(self._name_terminal) and not nameinfo.startswith(self._name_terminal) \
                and not WHITESPACERE.search(nameinfo):
            self.filename = nameinfo[:-1]
            self.name = nameinfo
        else:
            raise WrongMemberTypeException("Not a short GNU archive member.")

class GNULongMember(ArchiveMember):
    format = ArchiveMember.GNU

    _name_prefix = "/"
    _name_re = re.compile(r"^/(\d+)$")

    @property
    def name(self):
        offset = self.archive.strings.string_offset(self)
        return self._name_prefix + str(offset)
    @name.setter
    def name(self, value):
        self._name = value

    @property
    def filename(self):
        return self.archive.strings[self]
    @filename.setter
    def filename(self, value):
        self.archive.strings[self] = value

    def set_name_from_file(self, filename):
        if len(filename) >= 16 or WHITESPACERE.search(filename):
            self.filename = filename
        else:
            raise WrongMemberTypeException("Not a long GNU archive member.")

    def set_name_from_archive(self, nameinfo):
        m = self._name_re.match(nameinfo)
        if m:
            offset = int(m.group(1))
            self.archive.strings.map(self, offset)
        else:
            raise WrongMemberTypeException("Not a long GNU archive member.")

class GNUSymbolTable(ArchiveMember):
    format = ArchiveMember.GNU

    _name_literal = "/"

    def __init__(self, archive, path=None):
        super(GNUSymbolTable, self).__init__(archive, path)
        self.archive.symbols = self

    def init_from_path(self):
        self.name = self._name_literal
        self.filename = None
        self.date = int(time.time())
        self.uid = 0
        self.gid = 0
        self.mode = 0644
        self.offset = None

    # @property
    # def size(self):
    #     return self._size
    # @size.setter
    # def size(self, value):
    #     self._size = value

    def set_name_from_archive(self, nameinfo):
        if nameinfo == self._name_literal:
            self.filename = None
            self.name = nameinfo
        else:
            raise WrongMemberTypeException("Not a GNU symbol table archive member.")

class GNUStringTable(ArchiveMember):
    format = ArchiveMember.GNU

    _delimiter = "/\n"
    _name_literal = "//"

    def __init__(self, archive, path=None):
        super(GNUStringTable, self).__init__(archive, path)
        self.archive.strings = self

    @property
    def size(self):
        size = 0
        delimlen = len(self._delimiter)
        for i in self._items:
            size += len(i['filename']) + delimlen
        return size
    @size.setter
    def size(self, value):
        pass

    def init_from_file(self, path):
        self.name = self._name_literal
        self.filename = None
        self.date = int(time.time())
        self.uid = 0
        self.gid = 0
        self.mode = 0644
        self.offset = None

    def set_name_from_archive(self, nameinfo):
        if nameinfo == self._name_literal:
            self.name = nameinfo
            self.filename = None
        else:
            raise WrongMemberTypeException("Not a GNU string table archive member.")

    def map(self, member, offset):
        instream = self.archive.instream
        prevoffset = instream.tell()
        instream.seek(self.offset + offset)
        delimlen = len(self._delimiter)
        filename = instream.read(delimlen)
        while filename[-delimlen:] != self._delimiter:
            c = instream.read(1)
            if len(c) == 0:
                raise InvalidArchiveException("Unterminated string table.")
            filename += c
        filename = filename[:-2]
        self._items[member] = filename
        instream.seek(prevoffset)

    def __len__(self):
        return len(self._items)

    def __getitem__(self, member):
        return self._items[member]

    def __setitem__(self, member, filename):
        self._items[member] = filename

    def __delitem__(self, member):
        if member in self._items:
            del self._items[member]

    def __iter__(self):
        return self._items.__iter__()

class BSDShortMember(ArchiveMember):
    format = ArchiveMember.BSD

    def set_name_from_file(self, filename):
        if len(filename) <= 16 and not WHITESPACERE.search(filename):
            self.name = filename
            self.filename = filename
        else:
            raise WrongMemberTypeException("Not a short BSD archive member.")

    def set_name_from_archive(self, nameinfo):
        if not nameinfo.startswith(BSDSymbolTable._name_literal) and GNUShortMember._name_terminal not in nameinfo:
            self.name = nameinfo
            self.filename = nameinfo
        else:
            raise WrongMemberTypeException("Not a short BSD archive member.")

class BSDLongMember(ArchiveMember):
    format = ArchiveMember.BSD

    _name_prefix = "#1/"

    def __init__(self, archive, path=None):
        self.namelength = 0
        super(BSDLongMember, self).__init__(archive, path)

    @property
    def filesize(self):
        return self._size - self.namelength
    @filesize.setter
    def filesize(self, value):
        self._size = value + self.namelength

    @property
    def name(self):
        return self._name_prefix + str(self.namelength)
    @name.setter
    def name(self, value):
        pass

    def set_name_from_file(self, filename):
        if len(filename) > 16 or WHITESPACERE.search(filename):
            self.namelength = len(filename)
            self.filename = filename
        else:
            raise WrongMemberTypeException("Not a long BSD archive member.")

    def set_name_from_archive(self, nameinfo):
        if nameinfo.startswith(self._name_prefix):
            self.namelength = int(nameinfo[3:])
            self.filename = self.archive.instream.read(self.namelength)
            if self.filename.startswith(BSDSymbolTable._name_literal):
                raise WrongMemberTypeException("Not a long BSD archive member.")
        else:
            raise WrongMemberTypeException("Not a long BSD archive member.")

    def write_header(self):
        super(BSDLongMember, self).write_header()
        self.archive.outstream.write(self.filename)

class BSDSymbolTable(ArchiveMember):
    format = ArchiveMember.BSD

    _name_literal = "__.SYMDEF"
    _sorted_suffix = "SORTED"

    def __init__(self, archive, path=None):
        super(BSDSymbolTable, self).__init__(archive, path)
        self.archive.symbols = self

    @property
    def filesize(self):
        if self.filename is None:
            return self._size
        else:
            return self._size - self.namelength
    @filesize.setter
    def filesize(self, value):
        if self.filename is None:
            self._size = value
        else:
            self._size = value + self.namelength

    @property
    def name(self):
        if self.filename is None:
            return self._name_literal
        else:
            return BSDLongMember._name_prefix + str(self.namelength)
    @name.setter
    def name(self, value):
        pass

    def init_from_file(self, path):
        self.sorted = path == "sorted"
        if self.sorted:
            self.filename = self._name_literal + " " + self._sorted_suffix
            self.namelength = len(self.filename)
        else:
            self.filename = None
            self.namelength = 0

        self.date = int(time.time())
        self.uid = 0
        self.gid = 0
        self.mode = 0644
        self.offset = None

    def set_name_from_archive(self, nameinfo):
        if nameinfo == self._name_literal:
            self.filename = None
            self.namelength = 0
            self.sorted = False
        elif nameinfo.startswith(BSDLongMember._name_prefix):
            self.namelength = int(nameinfo[3:])
            self.filename = self.archive.instream.read(self.namelength)
            if not self.filename.startswith(self._name_literal):
                raise WrongMemberTypeException("Not a BSD symbol table archive member.")
            self.sorted = self.filename.endswith(self._sorted_suffix)
        else:
            raise WrongMemberTypeException("Not a BSD symbol table archive member.")

    def write_header(self):
        super(BSDSymbolTable, self).write_header()
        if self.filename is not None:
            self.archive.outstream.write(self.filename)

class Archive(object):
    _magic = "!<arch>\n"
    _body_pad = "\n"

    def __init__(self, format=ArchiveMember.GNU):
        self.reset()
        self.format = format

    def __repr__(self):
        formats = {
            None: "(none)",
            ArchiveMember.GNU: "GNU",
            ArchiveMember.BSD: "BSD"
        }
        return "<Archive(format={}, member_count={})>".format(formats[self._format], len(self.members))

    @property
    def strings(self):
        if self._strings is None and self.format == ArchiveMember.GNU:
            GNUStringTable(self, True)
        return self._strings

    @strings.setter
    def strings(self, value):
        self._strings = value

    @property
    def format(self):
        if self._format is None:
            raise InvalidArchiveException("No archive format specified or detected.")
        else:
            return self._format

    @format.setter
    def format(self, value):
        assert value == ArchiveMember.GNU or value == ArchiveMember.BSD
        self._format = value

    def reset(self):
        self._format = None
        self.symbols = None
        self._strings = None
        self.members = []
        self.instream = None
        self.outstream = None

    def load(self, filething):
        self.reset()

        log.info("Loading %r", filething)
        if isinstance(filething, str):
            self.instream = open(filething, "rb")
        else:
            self.instream = filething
        assert hasattr(self.instream, "read") and hasattr(self.instream, "tell") and hasattr(self.instream, "seek")

        magic = self.instream.read(len(self._magic))
        if magic != self._magic:
            raise InvalidArchiveException("Source of invalid archive: {}".format(self.instream))

        member = self.read_member()
        while member is not None:
            self.members.append(member)
            if self.instream.tell() % 2 == 1:
                padding = self.instream.read(len(self._body_pad))
                if padding != self._body_pad:
                    raise InvalidArchiveException("Source of invalid archive: {}".format(self.instream))
            member = self.read_member()

        log.info("Loaded %r", self)

    def read_member(self):
        member = None
        for cls in ArchiveMember.derived():
            oldoffset = self.instream.tell()
            log.debug("Starting at offset %u", oldoffset)
            try:
                member = cls(self)
                self.format = member.format
                self.instream.seek(member.offset + member.filesize)
                break
            except WrongMemberTypeException, e:
                log.debug("Wrong type for member: %s", e)
                self.instream.seek(oldoffset)
            except EOFError:
                log.debug("End of file")
                return None
        if member == None:
            raise WrongMemberTypeException("Unknown member type")

        log.info("Read member %r", member)
        return member
