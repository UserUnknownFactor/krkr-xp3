import os, zlib
from io import BytesIO
from array import array
from .encryption_parameters import encryption_parameters
from .file_entry import XP3FileEntry
try:
    from numpy import frombuffer, uint8, bitwise_and, bitwise_xor, right_shift, concatenate, dtype, fromstring, uint64, uint32, uint16, ubyte
    import math
    numpy = True
except ModuleNotFoundError:
    numpy = False
    
EXTRACT_INVALID = False

from .scrambling import KSScrambling

class XP3DecryptionError(Exception):
    pass

class XP3File(XP3FileEntry):
    """Wrapper around file entry with buffer access to be able to read the file"""

    def __init__(self, index_entry: XP3FileEntry, buffer, silent, use_numpy):
        super(XP3File, self).__init__(
            encryption=index_entry.encryption,
            time=index_entry.time,
            adlr=index_entry.adlr,
            segm=index_entry.segm,
            info=index_entry.info
        )
        self.buffer = buffer
        self.silent = silent
        self.use_numpy = use_numpy


    def read(self, encryption_type='none', raw=False):
        """Reads the file from buffer and return it's data"""

        if self.file_path == '' or 'This is a protected archive' in self.file_path:
            if not self.silent:
                print('! Not a file')
            return None
        
        all_data = b''
        for segment in self.segm:
            self.buffer.seek(segment.offset)
            data = self.buffer.read(segment.compressed_size)

            if segment.is_compressed:
                data = zlib.decompress(data)
            if len(data) != segment.uncompressed_size:
                raise AssertionError(len(data), segment.uncompressed_size)

            if self.is_encrypted or ("hidden" in encryption_parameters[encryption_type][0]):
                file_buffer = BytesIO(data)
                if encryption_type in ('none', None) and not raw:
                    raise XP3DecryptionError('File is encrypted and no encryption type was specified')
                self.xor(file_buffer, self.adler32, encryption_type, self.use_numpy)
                data = file_buffer.getvalue()
                file_buffer.close()

            all_data += data

        if self.adler32:
            checksum = zlib.adler32(all_data)
            if checksum != self.adler32:
                if not self.silent:
                    print(f'! Checksum error. Expected {hex(self.adler32)} got {hex(checksum)}')
                return all_data if EXTRACT_INVALID else None

        if os.path.splitext(self.file_path)[1] in ['.ks', '.tjs', '.wks', '.wtjs']:
            with KSScrambling(all_data) as scrambled:
                udata = scrambled.decode()
                if udata is None or udata == b'':
                    #if not self.silent:
                    #    print("! Not a scrambled Kirikiri file.")
                    pass
                else:
                    all_data = udata

        return all_data

    def extract(self, to='', name=None, encryption_type='none', raw=False):
        """
        Reads the data and saves the file to specified folder,
        if no location is specified, unpacks into folder with archive name (data.xp3, unpacks into data folder)
        """
        file = self.read(encryption_type=encryption_type, raw=raw)
        if file is None:
            return
        if not to:
            # Use archive name as output folder if it's not explicitly specified
            basename = os.path.basename(self.buffer.name)
            to = os.path.splitext(basename)[0]
        if not name:
            name = self.file_path
        to = os.path.join(to, name)

        dirname = os.path.dirname(to)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        with open(to, 'wb') as output:
            output.write(file)

    @staticmethod
    def xor(output_buffer, adler32: int, encryption_type: str, use_numpy: bool = False):
        """XOR the data, uses numpy if available"""
        enc_type, master_key, secondary_key, _ = encryption_parameters[encryption_type]
        # Read the encrypted data from buffer
        output_buffer.seek(0)
        data = output_buffer.read()

        # Use numpy if available
        if numpy and use_numpy and ("xor_full" in enc_type or "xor_plain" in enc_type or "xor_bytes" in enc_type) and not ("shr3" in enc_type or "xor-mix" in enc_type):
            key = None
            dt = dtype(uint8)
            if "xor_full" in enc_type:
                master_key = int.from_bytes(master_key) if master_key else 0
                adler_key = bitwise_xor(adler32, master_key) if master_key else adler32
                if adler_key:
                    key = bitwise_and(bitwise_xor(bitwise_xor(bitwise_xor(right_shift(adler_key, 24), right_shift(adler_key, 16)), right_shift(adler_key, 8)), adler_key), 0xFF)
                key = key if key else secondary_key
            elif "xor_plain" in enc_type:
                master_key = int.from_bytes(master_key) if master_key else 0
                adler_key = bitwise_xor(adler32, master_key) if master_key else adler32
                key = adler_key & 0xFF
                key = key if key else secondary_key
            elif "xor_bytes" in enc_type:
                if len(master_key):
                    key = fromstring((master_key * int(math.ceil( float(len(data))/float(len(master_key)) )))[:len(data)], dtype=dt)
                    #key = bitwise_xor(key, adler32 & 0xFF)
                else:
                    return
                #print(len(key), len(data))

            data = frombuffer(data, dtype=dt)

            if "xor-1st-b" in enc_type:
                first_byte_key = bitwise_and(adler_key, 0xFF)
                if not first_byte_key:
                    first_byte_key = bitwise_and(master_key, 0xFF)
                first = frombuffer(data[:1], dtype=uint8)
                first = bitwise_xor(first, first_byte_key)
                data = concatenate((first, frombuffer(data[1:], dtype=uint8)))

            data = bitwise_xor(data, key)
        else:
            master_key = int.from_bytes(master_key)
            adler_key = adler32 ^ master_key
            data = array('B', data)

            if "xor-1st-b" in enc_type:
                first_byte_key = adler_key & 0xFF
                if not first_byte_key: first_byte_key = master_key & 0xFF
                data[0] ^= first_byte_key

            # XOR the data
            if "xor_full" in enc_type:
                key = 0
                if adler_key:
                    key = (adler_key >> 24 ^ adler_key >> 16 ^ adler_key >> 8 ^ adler_key) & 0xFF
                key = key if key else secondary_key
                if key:
                    for i in range(0, len(data), 2): data[i] ^= key
            elif "xor_plain" in enc_type:
                key = adler_key & 0xFF
                if key:
                    for i in range(0, len(data)): data[i] ^= key
            elif "xor_byte" in enc_type:
                key = secondary_key & 0xFF
                for i in range(0, len(data)): data[i] ^= key
            elif "xor-p1-neg" in enc_type:
                key = adler_key & 0xFF
                for i in range(0, len(data)): data[i] = xor_p1_neg(data[i], key)
            elif "xor-mix" in enc_type:
                key = adler_key & 0xFF
                for i in range(0, len(data), 2): data[i] ^= key
                for i in range(1, len(data), 2): data[i] ^= i
            elif "shr3" in enc_type:
                for i in range(0, len(data)): data[i] ^= (adler_key >> 3) & 0xFF

        # Overwrite the buffer with decrypted/encrypted data
        output_buffer.seek(0)
        output_buffer.write(data.tobytes())

def plain_xor(nbyte, key): return (nbyte ^ key)
def xor_p1_neg(nbyte, key): return (nbyte ^ (key + 1) ^ 0xFF) & 0xFF
def xor_shr3(nbyte, key): return (nbyte ^ (key >> 3)) & 0xFF
