#!/usr/bin/env python3
import ed25519
import hashlib

# See https://github.com/nanocurrency/raiblocks/wiki/Design-features#signing-algorithm---ed25519

zero_seed = bytes([0]*32)

pubkey, privkey = ed25519.create_keypair(zero_seed)

# Incorrect, uses SHA-512
assert pubkey.hex().upper() == '3B6A27BCCEB6A42D62A3A8D02A6F0D73653215771DE243A63AC048A18B59DA29'


def create_context():
    # Note: needs Python 3.6 or newer
    return hashlib.blake2b(digest_size=32)
    
def init(context):
    pass
    
def update(context, arg):
    context.update(arg)
    
def final(context):
    return context.digest()
    
def hash(message):
    h = hashlib.blake2b(digest_size=64)
    h.update(message)
    return h.digest()

ed25519.custom_hash_function(create_context, init, update, final, hash)


pubkey, privkey = ed25519.create_keypair(zero_seed)

# Correct, uses Blake-2b
assert pubkey.hex().upper() == '19D3D919475DEED4696B5D13018151D1AF88B2BD3BCFF048B45031C1F36D1858'

