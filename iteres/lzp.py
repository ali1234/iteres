import os
import struct
import click
import tqdm

class LzpException(Exception):
    pass


class Lzp(object):

    def __init__(self, file):
        self._file = file
        self._nframes, self._width, self._height, self._framerate = struct.unpack('<IIII', self._file.read(16))
        self._file.seek(0x20, os.SEEK_SET)
        self.palette = tuple(struct.unpack('<BBB', self._file.read(3)) for _ in range(256))

        self._file.seek(-self._nframes*4, os.SEEK_END)
        self._length = self._file.tell()
        self._frame_offsets = struct.unpack(f'<{self._nframes}I', file.read(4*self._nframes))
        for o in self._frame_offsets:
            if o > self._length:
                raise LzpException('Frame table error.')

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def framerate(self):
        return self._framerate

    @property
    def nframes(self):
        return self._nframes

    def __getitem__(self, item):
        self._file.seek(self._frame_offsets[item], os.SEEK_SET)
        length, = struct.unpack('<I', self._file.read(4))
        f = self._file.read(length)

        pos = 0
        pixels = []
        while pos < len(f):
            #print(f'{pos:06x}:', end=' ')
            mask = f[pos]
            #print(f'{mask:02x}', end=' ')
            pos += 1
            for i in range(8):
                if mask & 1:
                    pixels.append(f[pos])
                    #print(f[pos:pos+1].hex(), end=' ')
                    pos += 1
                else:
                    cmd = f[pos:pos+2]
                    l = (cmd[1]&0xf) + 3
                    a = ((((cmd[1]&0xf0)<<4) | cmd[0]) + 18) & 0xfff
                    c = (len(pixels)&0xfffff000)
                    p = a | c
                    if p > len(pixels):
                        p -= 0x1000
                    #print(hex(l), hex(a), hex(c), hex(p), hex(len(pixels)))
                    #print(cmd.hex(), f'({hex(len(pixels))},{hex((len(pixels) - p) & 0xfff)},{hex(p)},{hex(l)})', end=' ')
                    for i in range(l):
                        try:
                            pixels.append(pixels[p])
                            p += 1
                        except IndexError:
                            print(p, len(pixels))
                            raise
                    pos += 2
                if pos == len(f):
                    break
                mask = mask >> 1
            #print('')
        #print(pos, len(f), len(pixels))
        return pixels


    def list(self):
        print(self._file.name)
        print(f'{self._width}x{self._height}, {self._framerate}fps, {self._nframes} frames.')
        for n, offset in enumerate(self._frame_offsets):
            print(f'Frame: {n:3d}, Offset: 0x{offset:08x}, Packed length: {len(self[n])} bytes')

    def debug(self):
        for n, c in enumerate(self.palette):
            print(hex(n), c)
        for n in range(self._nframes):
            f = self[n]
            for i in range(0,len(f),17):
                print(' '.join(f'{c:02x}' for c in f[i:i+17]))
            print('-----')

    def dump(self):
        nn = self._file.name.replace('.', '').replace('\\', '_').replace('/', '_')
        for n in range(self._nframes):
            with open(f'{nn}.{n:04x}.bin', 'wb') as o:
                o.write(self[n])

@click.group()
def itelzp():
    pass


@itelzp.command()
@click.argument('file', type=click.File(mode = 'rb'))
def list(file):

    try:
        l = Lzp(file)
        l.list()
    except LzpException as e:
        print(file.name, ':', e.args[0])
    except Exception as e:
        print(file.name, ':', e)


@itelzp.command()
@click.argument('file', type=click.File(mode = 'rb'))
def dump(file):

    try:
        l = Lzp(file)
        l.decode(60)
    except LzpException as e:
        print(file.name, ':', e.args[0])
    except Exception as e:
        print(file.name, ':', e)


@itelzp.command()
@click.argument('file', type=click.File(mode = 'rb'))
def play(file):

    import pygame
    from pygame.locals import QUIT, KEYDOWN, K_ESCAPE

    try:
        l = Lzp(file)

        pygame.init()
        screen = pygame.display.set_mode((l.width, l.height))
        pygame.display.set_caption('lzp')
        pygame.mouse.set_visible(0)

        clock = pygame.time.Clock()

        while 1:
          for n in range(l.nframes):
            clock.tick(l.framerate)
            for event in pygame.event.get():
                if event.type == QUIT:
                    return
                elif event.type == KEYDOWN and event.key == K_ESCAPE:
                    return

            f = bytes(l[n])

            surface = pygame.image.fromstring(f, (l.width, l.height), "P")
            surface.set_palette(l.palette)

            screen.blit(surface, (0, 0))
            pygame.display.flip()
            pygame.display.flip()


    except LzpException as e:
        print(file.name, ':', e.args[0])


@itelzp.command()
@click.argument('file', type=click.File(mode = 'rb'))
@click.option('-f', '--format', type=str, default='gif')
def convert(file, format):
    from PIL import Image

    nn = file.name.replace('.', '').replace('\\', '_').replace('/', '_')

    try:
        l = Lzp(file)
        images = []
        for n in tqdm.tqdm(range(l.nframes), unit='frames', desc=nn):
            im = Image.frombytes('P', (l.width, l.height), bytes(l[n]))
            im.putpalette(b''.join(bytes(c) for c in l.palette))
            images.append(im)

        images[0].save(f'{nn}.{format}', save_all=True, append_images=images[1:],
                       optimize=False, duration=1000//l.framerate, loop=0)

    except LzpException as e:
        print(file.name, ':', e.args[0])
