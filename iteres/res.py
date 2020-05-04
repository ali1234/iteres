import os
import pathlib
import struct
import click
import tqdm
from collections import defaultdict


class ResException(Exception):
    pass


class Res(object):

    def __init__(self, file):
        # Every resource file begins with the string 'ITERES'
        self._file = file

        self._file.seek(0, os.SEEK_END)
        self._length = self._file.tell()
        self._file.seek(0, os.SEEK_SET)

        magic = self._file.read(6)
        if magic != b'ITERES':
            raise ResException('Bad file magic.')

        blocksize, headerblocks, entries = struct.unpack('<III', self._file.read(12))
        headerend = blocksize * headerblocks

        self._filetable = []
        for n in range(entries):
            length, offset, pathlen = struct.unpack('<III', file.read(12))
            if (offset + length) > self._length:
                raise ResException('File table error.')
            try:
                path = pathlib.Path(pathlib.PureWindowsPath(file.read(pathlen)[:-1].decode('ascii')))
                self._filetable.append((headerend+offset, length, path))
            except UnicodeDecodeError:
                raise ResException('Invalid file name.')

    def extract(self, dest = '.'):
        dest = pathlib.Path(dest)
        for offset, length, path in tqdm.tqdm(self._filetable):
            self._file.seek(offset, os.SEEK_SET)
            data = self._file.read(length)
            (dest / path).parent.mkdir(parents=True, exist_ok=True)
            (dest / path).write_bytes(data)

    def list(self):
        print(self._file.name, '-', len(self._filetable), 'files.')
        for offset, length, path in self._filetable:
            print(f'{str(path)+" ":.<60s}{" " + str(length) + " bytes":.>18s}')


@click.group()
def iteres():
    pass


@iteres.command()
@click.argument('file', type=click.File(mode = 'rb'))
def list(file):
    try:
        r = Res(file)
        r.list()
    except ResException as e:
        print(file.name, ':', e.args[0])


@iteres.command()
@click.argument('file', type=click.File(mode = 'rb'))
def extract(file):
    try:
        r = Res(file)
        r.extract()
    except ResException as e:
        print(file.name, ':', e.args[0])


if __name__ == '__main__':
    iteres()
