import zlib, struct, sys
from io import BytesIO

UTF_16LE_BOM = b'\xFF\xFE'

class KSScrambling:
    """Handles scrambled script files."""
    def __init__(self, buffer: BytesIO = None, silent: bool = False, use_numpy: bool = True):
        """
        :param buffer: Buffer object to read/write data
        :param silent: Supress prints
        :param use_numpy: Use Numpy if available
        """
        if not buffer: buffer = b''
        elif buffer[0:2] == UTF_16LE_BOM: #remove BOM if present
            buffer = buffer[2:]
        self.buffer = BytesIO(buffer)
        self.silent = silent
        self.use_numpy = use_numpy

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.buffer.close()

    def mode0(self):
        data = bytearray(self.buffer.read())
        for i in range(0, len(data) - 1, 2):
            if (data[i + 1] == 0 and data[i] < 0x20):
                continue
            data[i + 1] ^= data[i] & 0b11111110
            data[i] ^= 1
        self.buffer.seek(0)
        return data

    def mode1(self):
        data = bytearray(self.buffer.read())
        for i in range(0, len(data) - 1, 2):
            c = (data[i] | (data[i + 1] << 8)) & 0xFFFF
            c = (((c & 0b1010101010101010) >> 1) | ((c & 0b101010101010101) << 1)) & 0xFFFF
            data[i] = c & 0xFF
            data[i + 1] = (c >> 8) & 0xFF
        self.buffer.seek(0)
        return data

    def decompress(self):
        compressed_length, uncompressed_length, header = struct.unpack('<QQH', self.buffer.read(8+8+2))
        self.buffer.seek(16, 0)
        data = self.buffer.read(sys.getsizeof(self.buffer) - self.buffer.tell())
        self.buffer.seek(0)
        return zlib.decompress(data)

    def compress(self):
        data = self.buffer.read(sys.getsizeof(self.buffer) - self.buffer.tell())
        compressed_data = zlib.compress(data)
        self.buffer.seek(0)
        self.buffer.write(struct.pack('<QQ', len(compressed_data), len(data)))
        self.buffer.write(compressed_data)
        self.buffer.seek(0)
        return self.buffer.read()

    def decode(self):
        """Descramble file"""
        magic = self.buffer.read(2)
        if (magic != b'\xFE\xFE'):
            return None
        mode, = struct.unpack('B', self.buffer.read(1))
        bom = self.buffer.read(2)
        if (bom != UTF_16LE_BOM):
            return None

        self.buffer.seek(5, 0)
        if mode == 0:
            utf16 = self.mode0()
        elif mode == 1:
            utf16 = self.mode1()
        elif mode == 2:
            utf16 = self.decompress()
        else:
            print("File uses unsupported scrambling mode {mode}".format(mode=mode))
            self.buffer.seek(0)
            return None

        return UTF_16LE_BOM + utf16
    
    def encode(self, mode=1):
        """Scramble file"""
        with BytesIO() as temp:
            temp.write(b'\xFE\xFE')
            temp.write(struct.pack('B', mode))
            temp.write(UTF_16LE_BOM)
    
            if mode == 0:
                temp.write(self.mode0())
            elif mode == 1:
                temp.write(self.mode1())
            elif mode == 2:
                temp.write(self.compress())
            else:
                print("Unsupported scrambling mode {mode} provided".format(mode=mode))
                self.buffer.seek(0)
                return None

            temp.seek(0)
            return temp.read()
