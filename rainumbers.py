#!/usr/bin/env python3
# After numbers.cpp
import hashlib

def bin2hex(s):
    assert isinstance(s, bytes)
    r = []
    for c in s:
        r.append('%02x' % c)
    return ''.join(r).upper()
    
def int2hex(v):
    print(v)
    assert isinstance(v, int)
    s = hex(v)
    assert s.startswith('0x')
    return s[2:].upper()
    

def bin2balance(b):
    """Mxrb (a.k.a. XRB)"""
    assert isinstance(b, bytes)
    return 1.0 * int.from_bytes(b, 'big') / (10**24 * 10**6)
    
    
base58_reverse = "~012345678~~~~~~~9:;<=>?@~ABCDE~FGHIJKLMNOP~~~~~~QRSTUVWXYZ[~\\]^_`abcdefghi"

def base58_decode(value):
    assert isinstance(value, str) and len(value) == 1
    assert value >= '0'
    assert value <= '~'
    return base58_reverse[ord(value) - 0x30] - 0x30
    

account_lookup = "13456789abcdefghijkmnopqrstuwxyz"
account_reverse = "~0~1234567~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~89:;<=>?@AB~CDEFGHIJK~LMNO~~~~~"

def account_encode(value):
    assert isinstance(value, int)
    assert value < 32
    return account_lookup[value]

def account_decode(value):
    assert isinstance(value, str) and len(value) == 1
    assert value >= '0'
    assert value <= '~'
    return chr(ord(account_reverse[ord(value) - 0x30]) - 0x30)

def decode_account(source_a):
    assert len(source_a) == 64
    assert source_a.startswith('xrb_') or source_a.startswith('xrb-') 
    
    number_l = 0
    
    for character in source_a[4:]:
        
        if ord(character) < 0x30 or ord(character) >= 0x80:
            raise ValueError('Character out of range')
            
        byte = account_decode(character)
        if byte == '~':
            raise ValueError('Invalid character')
            
        number_l <<= 5
        number_l += ord(byte)
        
    account = number_l >> 40
    check = number_l & 0xffffffffff

    # Digest to check is in the lowest 40 bits of the address
    hash = hashlib.blake2b(digest_size=5)
    hash.update(int.to_bytes(account, length=32, byteorder='big'))
    validation = hash.digest()
    
    assert check.to_bytes(length=5, byteorder='little') == validation
    
    """
    if (!result)
    {
        *this = (number_l >> 40).convert_to <rai::uint256_t> ();
        uint64_t check (number_l.convert_to <uint64_t> ());
        check &=  0xffffffffff;
        uint64_t validation (0);
        blake2b_state hash;
        blake2b_init (&hash, 5);
        blake2b_update (&hash, bytes.data (), bytes.size ());
        blake2b_final (&hash, reinterpret_cast <uint8_t *> (&validation), 5);
        result = check != validation;
    }
    """
    
    return account

def encode_account(account):
    
    assert isinstance(account, bytes)
    assert len(account) == 32
    
    hash = hashlib.blake2b(digest_size=5)
    hash.update(account)
    check = hash.digest()
        
    check = int.from_bytes(check, byteorder='big').to_bytes(length=5, byteorder='little')

    number = account + check    # concatenate byte strings
    number = int.from_bytes(number, byteorder='big')
    
    destination = ''
    
    for i in range(60):
        r = number & 0x1f
        number >>= 5
        destination += account_encode(r)
        
    destination += "_brx"
    
    return destination[::-1]


if __name__ == '__main__':
    
    A = 'xrb_1ziq3bxdo49abq5nii4qxq6pho1z788qtqias1h3mb1xojnisj96kibyh8xx'
    print(A)
    
    a = decode_account(A)
    print (a, int2hex(a))
    
    a = a.to_bytes(length=32, byteorder='big')
    print(encode_account(a))
    
    print(bin2balance(b'00000000000000000000000000000000'))
