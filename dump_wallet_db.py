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

import os, time
from enum import Enum
from struct import unpack
import lmdb, numpy
from rainumbers import *

"""
xrb_1ziq3bxdo49abq5nii4qxq6pho1z788qtqias1h3mb1xojnisj96kibyh8xx
received
    27340438 xrb
from
    xrb_31a51k53fdzam7bhrgi4b67py9o7wp33rec1hi7k6z1wsgh8oagqs7bui9p1
hash
    870E346AB08AC27A4B6413323BA129654783835DE9132FC0BF7ACE0D22273625
"""

"""
128 bits = 16 bytes
256 bits = 32 bytes
512 bits = 64 bytes


From lib/numbers.hpp:

amount, balance: 128 bit
account: 256 bit
block_hash: 256 bit
public_key, private_key, secret_key: 256 bit
checksum: 256 bit
signature: 512 bit

From class block_store in secure.hpp/.cpp:

accounts:
    account (32) -> block_hash (32), representative (block hash where rep was last set?), balance (32), timestamp (?)
    Account to head block, representative, balance, last_change
blocks_info:
    block_hash -> account, balance                               
    Blocks info
change:
    block_hash -> change_block
checksum:
    (uint56_t, uint8_t) -> block_hash                            
    Mapping of region to checksum
frontiers: 
    block_hash (32) -> account (32)
    Maps head blocks to owning account
meta:
    uint256_union -> ?											
    Meta information about block store
pending:
    block_hash (64?) -> sender, amount, destination    
    account, block_hash -> ...
    Pending blocks to sender account, amount, destination account
receive:
    block_hash -> receive_block
representation:
    account -> weight                                            
    Representation
send:
    block_hash -> send_block
unchecked:
    block_hash -> block                                          
    Unchecked bootstrap blocks
unsynched:
    block_hash -> ?                                               
    Blocks that haven't been broadcast
vote:
    account -> uint64_t											
    Highest vote observed for account
    
    
Subdb "unchecked" has MDB_DUPSORT set ("use sorted duplicates")

"""

"""
*** accounts ***
262068 records
key (min, max, median):  32 32 32.0
value (min, max, median):  128 128 128.0
*** blocks_info ***
97224 records
key (min, max, median):  32 32 32.0
value (min, max, median):  48 48 48.0
*** change ***
12041 records
key (min, max, median):  32 32 32.0
value (min, max, median):  168 168 168.0
*** checksum ***
1 records
key (min, max, median):  8 8 8.0
value (min, max, median):  32 32 32.0
*** frontiers ***
262068 records
key (min, max, median):  32 32 32.0
value (min, max, median):  32 32 32.0
*** meta ***
1 records
key (min, max, median):  32 32 32.0
value (min, max, median):  32 32 32.0
*** open ***
262068 records
key (min, max, median):  32 32 32.0
value (min, max, median):  200 200 200.0
*** pending ***
42130 records
key (min, max, median):  64 64 64.0
value (min, max, median):  48 48 48.0
*** receive ***
2020441 records
key (min, max, median):  32 32 32.0
value (min, max, median):  168 168 168.0
*** representation ***
4003 records
key (min, max, median):  32 32 32.0
value (min, max, median):  16 16 16.0
*** send ***
2324638 records
key (min, max, median):  32 32 32.0
value (min, max, median):  184 184 184.0
*** unchecked ***
19523 records
key (min, max, median):  32 32 32.0
value (min, max, median):  137 169 153.0
*** unsynced ***
0 records
*** vote ***
144 records
key (min, max, median):  32 32 32.0
value (min, max, median):  241 273 257.0

"""


DATADIR = 'RaiBlocks'
DBPREFIX = 'data.ldb'

SUBDBS = ['accounts', 'blocks_info', 'change', 'checksum', 'frontiers', 'meta', 'open', 'pending', 'receive', 'representation', 'send', 'unchecked', 'unsynced', 'vote']
SUBDBS = ['open']


env = lmdb.Environment(
        os.path.join(os.environ['HOME'],DATADIR,DBPREFIX), subdir=False, readonly=True,
        map_size=10*1024*1024*1024, max_dbs=16)

# XXX not used yet
# lib/blocks.hpp, enum class block_type
class BlockType(Enum):
    INVALID = 0
    NOT_A_BLOCK = 1
    SEND = 2
    RECEIVE = 3
    OPEN = 4
    CHANGE = 5
    
    
def find_block_type(blockhash, value=False):
    
    assert isinstance(blockhash, str)
    
    blockhash = hex2bin(blockhash)
    
    # Roughly in order of decreasing occurrence
    for subdbname in ['send', 'receive', 'open', 'change', 'vote']:
        
        subdb = env.open_db(subdbname.encode())

        with env.begin(write=False) as tx:
            
            cur = tx.cursor(subdb)
            if cur.set_range(blockhash):
                if value:
                    return subdbname, cur.value()
                return subdbname
            
    return None
    
#print(find_block_type('870E346AB08AC27A4B6413323BA129654783835DE9132FC0BF7ACE0D22273625'))
#doh





        
for subdbname in SUBDBS:
    
    subdb = env.open_db(subdbname.encode())

    with env.begin(write=False) as tx:
        cur = tx.cursor(subdb)
        cur.first()
        
        key_len = []
        value_len = []
        num_records = 0
        
        for key, value in cur:
            
            klen = len(key)
            vlen = len(value)
            key_len.append(klen)
            value_len.append(vlen)
              
            print('%s [%d bytes] -> %s [%d bytes]' % \
                (bin2hex(key), klen, bin2hex(value), vlen))
                
            if subdbname == 'accounts':                      
                # secure.cpp, rai::account_info::serialize()
    
                head_block = value[:32]
                representative = value[32:64]
                open_block = value[64:96]
                balance = value[96:112]
                modified = unpack('<Q', value[112:120])[0]
                block_count = unpack('<Q', value[120:128])[0]
                assert len(value[128:]) == 0
                
                print('Account %s (%s)' % (bin2hex(key), encode_account(key)))
                print('... head block %s' % bin2hex(head_block))
                print('... representative %s (%s)' % (bin2hex(representative), encode_account(representative)))
                print('... open block %s' % bin2hex(open_block))
                print('... balance %s (%.6f Mxrb)' % (bin2hex(balance), bin2balance_mxrb(balance)))
                print('... modified %d (%s LOCAL)' % (modified, time.asctime(time.localtime(modified))))
                print('... block_count %d' % block_count)
                
            elif subdbname == 'blocks_info':                      
                # secure.hpp, class rai::block_info
                # XXX unclear what is stored exactly
    
                account = value[:32]
                balance = value[32:48]
                assert len(value[48:]) == 0
                
                print('Block info %s' % bin2hex(key))
                print('... account %s (%s)' % (bin2hex(account), encode_account(account)))
                print('... balance %s (%.6f Mxrb)' % (bin2hex(balance), bin2balance_mxrb(balance)))
                
            elif subdbname == 'frontiers':       
                # Key is last block in the account chain
    
                account = value[:32]
                assert len(value[32:]) == 0
                
                print('Frontier %s' % bin2hex(key))
                print('... account %s (%s)' % (bin2hex(account), encode_account(account)))
                
            elif subdbname == 'change':
                # blocks.cpp, deserialize_block(stream, type), rai::change_block members
                
                previous_block = value[:32]
                representative = value[32:64]
                signature = value[64:128]
                work = unpack('<Q', value[128:136])[0]
                successor = value[136:168]
                assert len(value[168:]) == 0
                
                print('Change block %s' % bin2hex(key))
                print('... previous block %s' % bin2hex(previous_block))
                print('... representative %s (%s)' % (bin2hex(representative), encode_account(representative)))
                print('... signature %s' % bin2hex(signature))
                print('... work %08x' % work)
                print('... successor %s' % bin2hex(successor))
            
            elif subdbname == 'open':
                # blocks.cpp, deserialize_block(stream, type), rai::open_block members
                
                source_block = value[:32]
                representative = value[32:64]
                account = value[64:96]
                signature = value[96:160]
                work = unpack('<Q', value[160:168])[0]
                successor = value[168:200]
                assert len(value[200:]) == 0
                
                print('Open block %s' % bin2hex(key))
                print('... source block %s' % bin2hex(source_block))
                print('... representative %s (%s)' % (bin2hex(representative), encode_account(representative)))
                print('... account %s (%s)' % (bin2hex(account), encode_account(account)))
                print('... signature %s' % bin2hex(signature))
                print('... work %08x' % work)
                print('... successor %s' % bin2hex(successor))
            
            elif subdbname == 'pending':       
                # secure.hpp, class pending_info

                assert len(key) == 64
                destination = key[:32]
                block = key[32:]
    
                sender = value[:32]
                amount = value[32:48]
                assert len(value[48:]) == 0
                
                print('pending %s' % bin2hex(key))
                print('.k. destination %s (%s)' % (bin2hex(destination), encode_account(destination)))
                print('.k. block %s' % bin2hex(block))
                print('... sender %s (%s)' % (bin2hex(sender), encode_account(sender)))
                print('... amount %s (%.6f Mxrb)' % (bin2hex(amount), bin2balance_mxrb(amount)))
                #print('... destination %s (%s)' % (bin2hex(destination), encode_account(destination)))
                
            elif subdbname == 'receive':
                # blocks.cpp, deserialize_block(stream, type), rai::receive_block members
                
                previous_block = value[:32]
                source_block = value[32:64]
                signature = value[64:128]
                work = unpack('<Q', value[128:136])[0]
                successor = value[136:168]
                assert len(value[168:]) == 0
                
                print('Receive block %s' % bin2hex(key))
                print('... previous block %s' % bin2hex(previous_block))
                print('... source block %s' % bin2hex(source_block))
                print('... signature %s' % bin2hex(signature))
                print('... work %08x' % work)
                print('... successor %s' % bin2hex(successor))
                
            elif subdbname == 'representation':
                
                weight = value[:16]
                assert len(value[16:]) == 0
                
                print('Representation %s (%s)' % (bin2hex(key), encode_account(key)))
                print('... weight %.6f' % bin2balance_mxrb(weight))
                
            elif subdbname == 'send':
                # blocks.cpp, deserialize_block(stream, type), rai::send_block members
                
                previous_block = value[:32]
                destination = value[32:64]
                balance = value[64:80]
                signature = value[80:144]
                work = unpack('<Q', value[144:152])[0]
                successor = value[152:184]
                assert len(value[184:]) == 0
                
                print('Send block %s' % bin2hex(key))
                print('... previous block %s' % bin2hex(previous_block))
                print('... destination %s (%s)' % (destination, encode_account(destination)))
                print('... balance %s (%.6f Mxrb)' % (bin2hex(balance), bin2balance_mxrb(balance)))
                print('... signature %s' % bin2hex(signature))
                print('... work %08x' % work)
                print('... successor %s' % bin2hex(successor))
                
            elif subdbname == 'unchecked':
                
                block = value
                
                print('Unchecked block %s' % bin2hex(key))
                print('... %s' % bin2hex(block))
     
            elif subdbname == 'unsynced':
                
                block = value
                
                print('Unsynced block %s' % bin2hex(key))
                print('... %s' % bin2hex(block))
                
            elif subdbname == 'vote':
                # secure.cpp, vote::serialize()
                
                account = value[:32]
                signature = value[32:96]
                sequence_number = unpack('<Q', value[96:104])[0]
                successor = value[152:184]
                #assert len(value[184:]) == 0
                
                print('Vote block %s' % bin2hex(key))
                print('... voting account %s (%s)' % (bin2hex(account), encode_account(account)))
                print('... signature %s' % bin2hex(signature))
                print('... sequence_number %08x' % sequence_number)
                print('... block %s' % bin2hex(value[104:]))
                
            num_records += 1
                
    key_len = numpy.array(key_len, dtype=numpy.uint32)
    value_len = numpy.array(value_len, dtype=numpy.uint32)

    print('*** %s ***' % subdbname)
    print('%d records' % num_records)
    if num_records > 0:
        print('key (min, max, median)  : [%d, %d]; median = %.1f' % (numpy.min(key_len), numpy.max(key_len), numpy.median(key_len)))
        print('value (min, max, median): [%d, %d]; median = %.1f' % (numpy.min(value_len), numpy.max(value_len), numpy.median(value_len)))
