import argparse
import sys
import os

from dataclasses import dataclass, field
from enum import Enum

arg_parser = argparse.ArgumentParser(
    prog='Pak',
    description='Manipulates data with JPEG images',
    epilog='Made with love by github.com/richardcss',
    allow_abbrev=False,
)

arg_group = arg_parser.add_mutually_exclusive_group(required=True)

arg_group.add_argument(
    '-i',
    '--inject',
    nargs=2,
    metavar=('SOURCE', 'DEST'),
    help='specifies the JPEG file to be injected with data'
)

arg_group.add_argument(
    '-e',
    '--extract',
    nargs=2,
    metavar=('SOURCE', 'DEST'),
    help='specifies the JPEG file to extract data from',
)

arg_group.add_argument(
    '-c',
    '--clear',
    metavar='image',
    help='specifies the JPEG file to delete the injected data from'
)

arg_parser.add_argument(
    '-v',
    '--verbose',
    action='store_true',
    help='operates verbosely'
)

args = arg_parser.parse_args()


class FileType(Enum):
    ZIP = 'zip'
    SEVENZIP = '7z'


@dataclass(init=True)
class FileParser():
    image_path: str
    file_type: FileType = field(init=False, default=None)
    byte_stream: str = field(init=False)

    def __post_init__(self):
        try:
            with open(self.image_path, 'rb') as image:
                self.byte_stream = image.read()

                # Checks if the file has the signature of a JPEG file
                if not self.byte_stream[:2] == bytes.fromhex('FFD8') and not self.byte_stream[-2:] == bytes.fromhex('FFD9'):
                    sys.stderr.write('The file specified is not a valid JPEG')
                    sys.exit()

        except FileNotFoundError:
            sys.stderr.write('The file specified does not exist')
            sys.exit()

    def inject(self, file_path):
        if not os.path.exists(file_path):
            sys.stderr.write('The file specified does not exist')
            sys.exit()

        if not self._is_empty():
            sys.stderr.write(
                'The image already contains injected data!\nExiting...')
            sys.exit()

        with open(file_path, 'rb') as file:
            content = file.read()
            with open(self.image_path, 'ab') as image:
                if args.verbose:
                    sys.stdout.write(
                        f'Writing {os.stat(file_path).st_size} bytes of data into {self.image_path}...\n')
                image.write(content)
            if args.verbose:
                sys.stdout.write(
                    f'Data wrote into {self.image_path} successfully!')

    def extract(self, file_path='extracted'):
        if self._is_empty():
            sys.stderr.write('The specified image is empty!\nExiting...')
            sys.exit()

        file_ext = self._get_file_ext()

        with open(self.image_path, 'rb') as image:
            content = image.read()
            offset = content.index(bytes.fromhex('FFD9')) + 2
            image.seek(offset)

            with open(f'{file_path}.{file_ext.value}', 'wb') as file:
                content = image.read()
                if args.verbose:
                    sys.stdout.write(
                        f'Extracting {len(content)} bytes of data from {self.image_path}...\n')

                file.write(content)

        if args.verbose:
            sys.stdout.write(
                f'Data extracted into \'{file_path}.{file_ext.value}\' successfully!')

    def clear(self):
        if self._is_empty():
            sys.stderr.write('The specified image is empty!\nExiting...')
            sys.exit()

        with open(self.image_path, 'rb+') as image:
            content = image.read()
            offset = content.index(bytes.fromhex('FFD9')) + 2
            bytes_cleaned = len(content[offset:])
            content = content[:offset]
            image.truncate(0)
            image.seek(0)
            image.write(content)
            sys.stdout.write(
                f'Cleaned {bytes_cleaned} bytes of data successfully!')

    def _get_file_ext(self) -> FileType:
        with open(self.image_path, 'rb') as image:
            content = image.read()
            offset = content.index(bytes.fromhex('FFD9')) + 2
            # Reads the first four hex digits to check the file extension
            content = content[offset:offset + 4]

            if content == bytes.fromhex('377ABCAF'):
                return FileType.SEVENZIP
            elif content == bytes.fromhex('504B0304'):
                return FileType.ZIP

    def _is_empty(self) -> bool:
        with open(self.image_path, 'rb') as image:
            content = image.read()
            # Reads everything after 0xFFD9
            injected_data = content[content.index(bytes.fromhex('FFD9')) + 2:]

            return not bool(injected_data)


if __name__ == '__main__':
    if args.inject:
        file_parser = FileParser(args.inject[1])
        file_parser.inject(args.inject[0])
    elif args.extract:
        file_parser = FileParser(args.extract[0])
        file_parser.extract(args.extract[1])
    else:
        file_parser = FileParser(args.clear)
        file_parser.clear()
