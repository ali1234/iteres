from setuptools import setup

setup(
    name='iteres',
    version='0.1',
    packages=['iteres'],
    url='https://github.com/ali1234/iteres',
    license='',
    author='Alistair Buxton',
    author_email='a.j.buxton@gmail.com',
    description='COnverter for ITE resource files',
    install_requires=['click', 'tqdm', 'pygame', 'pillow'],
    entry_points={
        'console_scripts': [
            'iteres = iteres.res:iteres',
            'itecgf = iteres.cgf:itecgf',
            'itelzp = iteres.lzp:itelzp',
        ],
    }
)
