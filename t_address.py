#!/usr/bin/env python2
account_lookup = '13456789abcdefghijkmnopqrstuwxyz'
account_reverse = '~0~1234567~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~89:;<=>?@AB~CDEFGHIJK~LMNO~~~~~'

def account_encode(value):
    assert value < 32
    result = account_lookup[value]
    return result
    
def account_decode(value):
    assert value >= '0' and value <= '~'
    return ord(account_reverse[ord(value)-0x30]) - 0x30
    
for i in xrange(32):
    e = account_encode(i)
    d = account_decode(e)
    print i, e, d
    assert i == d