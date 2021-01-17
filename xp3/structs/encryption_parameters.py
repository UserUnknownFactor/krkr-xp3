encryption_parameters = {
                       # XOR algorithm, master key, secondary key, wirtten segment name
    'none':            ("xor_plain", 0x00000000, 0x00, b'eliF'),
    'noop':            ("xor_full", 0x00000000, 0x00, b'eliF'), 
    'nekov1':       ("xor_full", 0x1548E29C, 0xD7, b'eliF'),
    'nekov1steam': ("xor_full", 0x44528B87, 0x23, b'eliF'),
    'nekov0':       ("xor_full, xor-1st-b", 0x1548E29C, 0xD7,  b'neko'),
    'nekov0steam': ("xor_full, xor-1st-b", 0x44528B87, 0x23,  b'neko'),
    'p1neg':       ("xor-p1-neg, scrambler1, hidden", 0x00000000, 0x00,  b'eliF')
}
