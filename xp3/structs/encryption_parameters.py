encryption_parameters = {
               # XOR algorithms, Master key, Secondary key, Segment name
    'none':    ["xor_plain", b'', 0x00, b'eliF'],
    'noop':    ["xor_full", b'', 0x00, b'eliF'], 
    'nekov1':  ["xor_full", b'\x15\x48\xE2\x9C', 0xD7, b'eliF'],
    'hidden':  ["xor_plain, hidden", b'', 0x00, b'eliF'],
    'hiddenf': ["xor_key, hidden", b'', 0x00, b'eliF'],
    'hiddenb': ["xor_bytes, hidden", b'', 0x00, b'eliF'],
    'p1neg':   ["xor-p1-neg, scrambler1, hidden", b'', 0x00,  b'eliF'],
    'shr3':    ["shr3, xor_key, hidden", b'', 0x00,  b'eliF'],
}
