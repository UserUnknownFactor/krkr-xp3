#!/usr/bin/env python
import os
from .xp3reader import XP3Reader
from .xp3writer import XP3Writer

class XP3(XP3Reader, XP3Writer):
    def __init__(self, target, mode='r', silent=False):
        self.mode = mode # for debugging convenience
        self.target = target

        if self._is_readmode:
            if isinstance(target, str):
                if not os.path.isfile(target):
                    raise FileNotFoundError
                self.target = open(target, 'rb')
            XP3Reader.__init__(self, self.target, silent, True)
        elif self._is_writemode:
            if isinstance(target, str):
                dir = os.path.dirname(target)
                if dir and not os.path.exists(dir):
                    os.makedirs(dir)
                self.target = open(target, 'wb')
            XP3Writer.__init__(self, self.target, silent, True)
        else:
            raise ValueError('Invalid operation mode')

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Write the file index in the archive as we leave the context manager"""
        if self._is_writemode:
            if not self.packed_up:
                self.pack_up()
            self.buffer.close()
        self.target.close()

    @property
    def _is_readmode(self):
        return True if self.mode == 'r' else False

    @property
    def _is_writemode(self):
        return True if self.mode == 'w' else False

    def unpack(self, to='', encryption_type='none'):
        """Unpack all files in the archive to a specified folder"""
        if not self._is_readmode:
            raise Exception('Archive is not open in reading mode')

        for file in self:
            try:
                if not self.silent:
                    print('| Unpacking {} ({} -> {} bytes)'.format(file.file_path,
                                                                    file.info.compressed_size,
                                                                    file.info.uncompressed_size))
                if os.path.isfile(os.path.join(to, file.file_path)):
                    print('! File {} already exists'.format(os.path.join(to, file.file_path)))
                else:
                    file.extract(to=to, encryption_type=encryption_type)
            except OSError:  # Usually because of long file names
                if not self.silent:
                    print('! Problem writing {}'.format(file.file_path))
        return self

    def add_folder(self, path, flatten: bool = False, encryption_type: str = None, save_timestamps: bool = False):
        if not self._is_writemode:
            raise Exception('Archive is not open in writing mode')
        for dirpath, dirs, filenames in os.walk(path):
            # Strip off the base directory and possible slash
            internal_root = dirpath[len(path) + 1:]
            # and make sure we're using forward slash as a separator
            internal_root = internal_root.split(os.sep)
            internal_root = '/'.join(internal_root)

            for filename in filenames:
                internal_filepath = internal_root + '/' + filename \
                                    if internal_root and not flatten \
                                    else filename
                self.add_file(os.path.join(dirpath, filename), internal_filepath, encryption_type, save_timestamps)

    def add_file(self, path, internal_filepath: str = None, encryption_type: str = None, save_timestamps: bool = False):
        """
        :param path: Path to file
        :param internal_filepath: Internal archive path to save file under (if not specified, file name is used)
        :param encryption_type: Encryption type to use
        :param save_timestamps: Save the file creating time into archive or not
        """
        if not self._is_writemode:
            raise Exception('Archive is not open in writing mode')

        if not os.path.exists(path):
            raise FileNotFoundError

        with open(path, 'rb') as buffer:
            data = buffer.read()
            if not internal_filepath:
                internal_filepath = os.path.basename(buffer.name)

        timestamp = 0 if not save_timestamps else round(os.path.getctime(path) * 1000)
        super().add(internal_filepath, data, encryption_type, timestamp)


def main():
    import argparse, sys
    from .structs.encryption_parameters import encryption_parameters
    VERSION_STR = "1.0.0"

    def input_filepath(path: str) -> str:
        if not os.path.exists(os.path.realpath(path)):
            print(f"ERROR: {path} dosn't exist or not accessible")
            sys.exit(2)
        return path

    parser = argparse.ArgumentParser(description=f"KiriKiri .xp3 archive unpack/repack tool v{VERSION_STR}")
    mode = parser.add_argument_group('operation mode').add_mutually_exclusive_group()
    mode.add_argument('-u', '--unpack', action='store_true', help='Unpack XP3 archive')
    mode.add_argument('-r', '--repack', action='store_true', help='Repack XP3 archive')
    parser.add_argument('-s', '--silent', action='store_true', default=False)
    parser.add_argument('-f', '--flatten', action='store_true', default=False,
                        help="""Ignore the subdirectories and pack the archive as if all files are in the root folder,
                        some games take only patches packed this way.
                        """)
    parser.add_argument('-i', '--index', action='store_true', help='Dump the file index of an archive')
    parser.add_argument('-c', '--cypher', choices=encryption_parameters.keys(), default='none',
                        help='Specify the cypher mode')
    parser.add_argument('input', type=input_filepath, help='File to unpack or folder to repack')
    parser.add_argument('output', help='Output folder to unpack into or output file to repack into')

    if len(sys.argv) < 2:
        parser.print_help(sys.stderr)
        sys.exit()
    args = parser.parse_args()


    is_silent = args.silent
    if args.unpack:
        with XP3(args.input, 'r', is_silent) as xp3:
            if args.index:
                if not is_silent:
                    print('Dumping index of {}'.format(args.output))
                xp3.file_index.unpack(args.output)
            else:
                if not is_silent:
                    print('Unpacking {} → {}'.format(args.input, os.path.abspath(args.output)))
                xp3.unpack(args.output, args.cypher)
    elif args.repack:
        with XP3(args.output, 'w', is_silent) as xp3:
            if not is_silent:
                print('Packing {} → {}'.format(os.path.abspath(args.input), args.output))
            xp3.add_folder(args.input, args.flatten, args.cypher)

if __name__ == '__main__':
    main()

