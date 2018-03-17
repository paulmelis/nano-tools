#!/usr/bin/env python3
import sys, hashlib, json, os
import ed25519
import rainumbers

# Set up blake2b

def create_context():
    # Note: needs Python 3.6 or newer
    return hashlib.blake2b(digest_size=64)
    
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



if len(sys.argv) != 2:
    print('usage: %s <blockhash>-<account>[-<description>].block' % sys.argv[1])
    sys.exit(0)

blockfile = sys.argv[1]

with open(blockfile, 'rt') as f:
    block = json.load(f)
    
print(block)

basename = os.path.splitext(os.path.split(blockfile)[-1])[0]

parts = basename.split('-')
blockhash = parts[0]
address = parts[1]

account = rainumbers.decode_account(address)
pubkey = account
print(address, '->', account.hex())

type = block['type']
work = bytes.fromhex(block['work'])
signature = bytes.fromhex(block['signature'])

if type == 'send':
    previous = bytes.fromhex(block['previous'])
    destination = rainumbers.decode_account(block['destination'])
    balance = bytes.fromhex(block['balance'])
    hashables = [previous, destination, balance]
elif type == 'receive':
    previous = bytes.fromhex(block['previous'])
    source = bytes.fromhex(block['source'])
    hashables = [previous, source]
elif type == 'open':
    source = bytes.fromhex(block['source'])
    representative = rainumbers.decode_account(block['representative'])
    a = rainumbers.decode_account(block['account'])
    assert a == account
    hashables = [source, representative, account]
elif type == 'change':
    previous = bytes.fromhex(block['previous'])
    representative = rainumbers.decode_account(block['representative'])
    hashables = [previous, representative]

# utx: account, previous, representative, balance, link

d = hashlib.blake2b(digest_size=32)
for h in hashables:
    d.update(h)
blockhash_computed = d.digest()

print('block hash (from file name) :', blockhash.lower())
print('block hash (computed)       :', blockhash_computed.hex())

ok = ed25519.verify(signature, blockhash_computed, pubkey)
print('Signature:', 'VERIFIED' if ok else 'FAILED')
