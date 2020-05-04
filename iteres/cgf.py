import os
import struct
import click


@click.group()
def itecgf():
    pass


@itecgf.command()
@click.argument('file', type=click.File(mode = 'rb'))
def dump(file):
    # Every CGF file begins with the string 'CGFF'

    file.seek(0, os.SEEK_END)
    length = file.tell()
    file.seek(0, os.SEEK_SET)

    magic = file.read(4)
    assert magic == b'CGFF', 'Bad file magic.'

    version, entries, headersize, datasize, format, version2 = struct.unpack('<IIIIII', file.read(24))
    assert version == 1 and version2 == 0, 'Unknown version'
    if format == 0:
        assert 28+headersize+datasize == length, 'Bad file size'
        assert entries*6*4 == headersize, 'Bad header size'

    offset = 0
    for n in range(entries):
        a, b, c, d, e, f = struct.unpack('<IIIIII', file.read(24))
        assert e in [0x2e, 0x26], 'Unknown flag'
        print(file.name, hex(a), hex(b), hex(c), hex(d), hex(e), hex(f), (f-offset))
        offset = f

if __name__ == '__main__':
    itecgf()
