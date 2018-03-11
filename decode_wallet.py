#!/usr/bin/env python3
#
# Copyright (c) 2018 Paul Melis
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# 
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import sys, getpass, json
import argon2
from Crypto.Cipher import AES
from Crypto.Util import Counter
from rainumbers import bin2hex, hex2bin

KEYLEN = 32     # bytes, i.e. 256 bits

# After rai/node/wallet.cpp
KEY_VERSION                         = '%064x' % 0       # Wallet version number
KEY_WALLET_SALT                     = '%064x' % 1       # Random number used to salt private key encryption
KEY_ENCRYPTED_WALLET_KEY            = '%064x' % 2       # Key used to encrypt wallet keys, encrypted itself by the user password
KEY_CHECK_VALUE                     = '%064x' % 3       # Check value used to see if password is valid
KEY_WALLET_REPRESENTATIVE           = '%064x' % 4       # Representative account to be used if we open a new account
KEY_WALLET_SEED_DETERMINISTIC_KEYS  = '%064x' % 5       # Wallet seed for deterministic key generation
KEY_INDEX_DETERMINISTIC_KEYS        = '%064x' % 6       # Current key index for deterministic keys

if len(sys.argv) != 2:
    print('usage: %s file.json' % sys.argv[0])
    sys.exit(-1)
    
# ~/RaiBlocks/backup/.....json
walletfile = sys.argv[1]

wallet = {}
with open(walletfile, 'rt') as f:
    wallet = json.loads(f.read())
    
#print(wallet)

version = int.from_bytes(hex2bin(wallet[KEY_VERSION]), byteorder='big')
assert version == 3

wallet_salt = hex2bin(wallet[KEY_WALLET_SALT])
encrypted_wallet_key = hex2bin(wallet[KEY_ENCRYPTED_WALLET_KEY])

initial_counter_value = int.from_bytes(wallet_salt[:16], byteorder='big')

# Get user password

user_password = getpass.getpass('Password: ')

# Derive key using Argon2
# Note: uses full wallet salt

derived_key = argon2.argon2_hash(user_password, wallet_salt, buflen=KEYLEN,
                    t=1, m=64*1024, p=1, argon_type=0)

#print(bin2hex(derived_key), '(derived key)')

# Get encrypted wallet key and decrypt it
# Note: uses only the first half of the salt for the CTR mode

counter = Counter.new(128, initial_value=initial_counter_value)
aes = AES.new(derived_key, AES.MODE_CTR, counter=counter)

decrypted_wallet_key = aes.decrypt(encrypted_wallet_key)

#print(bin2hex(decrypted_wallet_key))

# Password check: 
# - Encrypt zeros with the (decrypted) wallet key
# - Check against stored value
# - Also uses only the first half of the salt

counter = Counter.new(128, initial_value=initial_counter_value)
aes = AES.new(decrypted_wallet_key, AES.MODE_CTR, counter=counter)
result = aes.encrypt('\x00'*32)

result = bin2hex(result).upper()
check = wallet[KEY_CHECK_VALUE]

if result == check:
    #print(check)
    print('CORRECT')
else:
    print(result)
    print(check)
    print('INCORRECT')

