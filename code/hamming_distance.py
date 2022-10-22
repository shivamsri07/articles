"""
    val_1 => 2: 0010
    val_2 => 3: 0011

    No. of different bits: 1
"""

def hamming_distance(val_1, val_2):

    #do `xor` so that the different bits in val_1 and val_2 becomes set in the result
    xor = val_1 ^ val_2

    set_bits = 0
    #count set bits and right shift bits by 1
    while xor:
        set_bits += xor & 1

        xor >>= 1

    return set_bits


print(hamming_distance(2, 3)) # o/p => 1
