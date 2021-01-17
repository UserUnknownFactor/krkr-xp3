"""
KiriKiri XP3-archive unpack/repack tool
-----------

Unpacks an .xp3 archive to a directory or packs a directory, including all subdirectories, into an .xp3 archive. It supports basic cyphers and scrambling.

Link
`````
 `github <https://github.com/UserUnknownFactor/krkr-xp3>`_


"""
from setuptools import setup, find_packages
from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md')) as f: long_description = f.read()
with open(path.join(this_directory, 'requirements.txt')) as f: requirements = f.read().splitlines()

setup(
    name='krkr-xp3',
    version='1.0.0',
    url='https://github.com/UserUnknownFactor/krkr-xp3',
    license='MIT',
    author='UserUnknownFactor',
    author_email='noreply@example.com',
    description='Unpacks and packs .xp3 archives of KiriKiri engine',
    long_description=long_description,
    install_requires=requirements,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Other Audience',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Games/Entertainment',
    ],
    packages = find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts': ['xp3=xp3.xp3:main']
    }
)
