#!/usr/bin/env python3
import sys, os, time
from struct import unpack
import lmdb, apsw, numpy
import progressbar
from rainumbers import *

DATADIR = 'RaiBlocks'
DBPREFIX = 'data.ldb'
RAIBLOCKS_LMDB_DB = os.path.join(os.environ['HOME'], DATADIR, DBPREFIX)

# XXX Store for each block to which account chain it belongs, can reuse account ids for this.
# This gives a direct mapping from block to chain/account

SCHEMA = """
begin;

drop table if exists accounts;
drop table if exists blocks;

create table accounts (
    id          integer not null,
    address     text not null,      -- xrb_....   

    -- could store derived quantities, like
    -- number of blocks
    -- balance
    
    primary key(id),
    unique(address)
);

create table blocks (
    id          integer not null,
    hash        text not null,
    type        text not null,
    
    -- All blocks
    previous    integer,            -- Can be NULL for an open block
    next        integer,            -- "successor", called "next" to match "previous"
    signature   text not null,
    
    -- Depending on block type
    work            text,           -- change, open, receive, send
    representative  integer,        -- change
    source          integer,        -- open, receive
    destination     integer,        -- send
    balance         float,          -- Mxrb, float representation (not fully precise, 8 byte precision instead of needed 16 bytes)
    balance_raw     text,           -- raw, integer in string representation 
    account         integer,        -- open, vote
    --sequence_number integer,        -- vote
    --block           text,           -- vote
    
    primary key(id),
    unique(hash)
);

commit;
"""

CREATE_INDICES = """
create index accounts_address on accounts (address);

create index blocks_source on blocks (source);
create index blocks_destination on blocks (source);
create index blocks_account on blocks (account);
create index blocks_balance on blocks (balance);
create index blocks_next on blocks (next);
create index blocks_previous on blocks (previous);
create index blocks_type on blocks (type);
"""

dbfile = sys.argv[1]

sqldb = apsw.Connection(dbfile)
sqlcur = sqldb.cursor()
sqlcur.execute(SCHEMA)

# Map block hash (bytes) to integer ID (starting at 1)
block_ids = {}
next_block_id = 1

# Map account address ('xrb_...') to integer ID (starting at 1)
account_ids = {}
next_account_id = 1

def get_block_id(blockhash):
    # XXX this takes a bytes object, while get_account_id takes a string :-/
    
    if bin2hex(blockhash) == '0000000000000000000000000000000000000000000000000000000000000000':
        return None
    
    global next_block_id
    try:
        return block_ids[blockhash]
    except KeyError:
        block_ids[blockhash] = next_block_id
        next_block_id += 1
        return next_block_id-1

def get_account_id(address):
    assert address.startswith('xrb_') and len(address) == 64
    
    global next_account_id
    try:
        return account_ids[address]
    except KeyError:
        account_ids[address] = next_account_id
        next_account_id += 1
        return next_account_id-1


"""
def process_vote_entry(cur, key, value):
    
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
    
    sqlcur.execute('insert into blocks (hash, type, account, signature, sequence_number, block) values (?,?,?,?,?,?)',
        (bin2hex(key), 'vote', encode_account(account), bin2hex(signature), sequence_number, bin2hex(value[104:])))
"""

def process_open_entry(cur, key, value):
    
    # blocks.cpp, deserialize_block(stream, type), rai::open_block members

    source_block = value[:32]
    representative = value[32:64]
    account = value[64:96]
    signature = value[96:160]
    work = unpack('<Q', value[160:168])[0]
    successor = value[168:200]
    assert len(value[200:]) == 0
    
    """
    print('Open block %s' % bin2hex(key))
    print('... source block %s' % bin2hex(source_block))
    print('... representative %s (%s)' % (bin2hex(representative), encode_account(representative)))
    print('... account %s (%s)' % (bin2hex(account), encode_account(account)))
    print('... signature %s' % bin2hex(signature))
    print('... work %08x' % work)
    print('... successor %s' % bin2hex(successor))
    """
    
    block_id = get_block_id(key)
    
    hash = bin2hex(key)
    source_id = get_block_id(source_block)
    representative_id = get_account_id(encode_account(representative))
    account_id = get_account_id(encode_account(account))
    signature = bin2hex(signature)
    work = '%08x' % work
    successor_id = get_block_id(successor)
    
    # XXX work value
    
    sqlcur.execute('insert into blocks (id, hash, type, source, representative, account, signature, work, next) values (?,?,?,?,?,?,?,?,?)',
        (block_id, hash, 'open', source_id, representative_id, account_id, signature, work, successor_id))
  
def process_change_entry(cur, key, value):  
    
    # blocks.cpp, deserialize_block(stream, type), rai::change_block members
    
    previous_block = value[:32]
    representative = value[32:64]
    signature = value[64:128]
    work = unpack('<Q', value[128:136])[0]
    successor = value[136:168]
    assert len(value[168:]) == 0
    
    """
    print('Change block %s' % bin2hex(key))
    print('... previous block %s' % bin2hex(previous_block))
    print('... representative %s (%s)' % (bin2hex(representative), encode_account(representative)))
    print('... signature %s' % bin2hex(signature))
    print('... work %08x' % work)
    print('... successor %s' % bin2hex(successor))        
    """
    
    block_id = get_block_id(key)
    
    hash = bin2hex(key)
    previous_id = get_block_id(previous_block)
    representative_id = get_account_id(encode_account(representative))
    signature = bin2hex(signature)
    work = '%08x' % work
    successor_id = get_block_id(successor)
    
    sqlcur.execute('insert into blocks (id, hash, type, previous, representative, signature, work, next) values (?,?,?,?,?,?,?,?)',
        (block_id, hash, 'change', previous_id, representative, signature, work, successor_id))

def process_receive_entry(cur, key, value):
    
    # blocks.cpp, deserialize_block(stream, type), rai::receive_block members
    
    previous_block = value[:32]
    source_block = value[32:64]
    signature = value[64:128]
    work = unpack('<Q', value[128:136])[0]
    successor = value[136:168]
    assert len(value[168:]) == 0
    
    """
    print('Receive block %s' % bin2hex(key))
    print('... previous block %s' % bin2hex(previous_block))
    print('... source block %s' % bin2hex(source_block))
    print('... signature %s' % bin2hex(signature))
    print('... work %08x' % work)
    print('... successor %s' % bin2hex(successor))
    """
    
    block_id = get_block_id(key) # XXX _id
    
    hash = bin2hex(key)
    previous_id = get_block_id(previous_block)
    source_id = get_block_id(source_block)
    signature = bin2hex(signature)
    work = '%08x' % work
    successor_id = get_block_id(successor)
    
    sqlcur.execute('insert into blocks (id, hash, type, previous, source, signature, work, next) values (?,?,?,?,?,?,?,?)',
        (block_id, hash, 'receive', previous_id, source_id, signature, work, successor_id))

def process_send_entry(cur, key, value):

    # blocks.cpp, deserialize_block(stream, type), rai::send_block members
    
    previous_block = value[:32]
    destination = value[32:64]
    balance = value[64:80]
    signature = value[80:144]
    work = unpack('<Q', value[144:152])[0]
    successor = value[152:184]
    assert len(value[184:]) == 0
    
    """
    print('Send block %s' % bin2hex(key))
    print('... previous block %s' % bin2hex(previous_block))
    print('... destination %s (%s)' % (destination, encode_account(destination)))
    print('... balance %s (%.6f Mxrb)' % (bin2hex(balance), bin2balance_mxrb(balance)))
    print('... signature %s' % bin2hex(signature))
    print('... work %08x' % work)
    print('... successor %s' % bin2hex(successor))
    """
    
    block_id = get_block_id(key)
    
    balance_mxrb = bin2balance_mxrb(balance)
    balance_raw = bin2balance_raw(balance)
    
    hash = bin2hex(key)    
    previous_id = get_block_id(previous_block)
    destination_id = get_account_id(encode_account(destination))
    signature = bin2hex(signature)
    work = '%08x' % work
    successor_id = get_block_id(successor)
        
    # Note that we store balance_raw (a Python long) as a string
    sqlcur.execute('insert into blocks (id, hash, type, previous, destination, balance, balance_raw, signature, work, next) values (?,?,?,?,?,?,?,?,?,?)',
        (block_id, hash, 'send', previous_id, destination_id, balance_mxrb, str(balance_raw), signature, work, successor_id))


processor_functions = {
    'change'    : process_change_entry,
    'open'      : process_open_entry,
    'receive'   : process_receive_entry,
    'send'      : process_send_entry,
    #'vote': process_vote_entry,
}

env = lmdb.Environment(
        RAIBLOCKS_LMDB_DB, subdir=False,
        map_size=10*1024*1024*1024, max_dbs=16,
        readonly=True)
      
"""                    
# Prepare by reading per-block info, which we need later

# Key is block id
block_to_account = {}   # Account id
block_to_balance = {}   # In raw (long value)

subdb = env.open_db(b'blocks_info')

with env.begin(write=False) as tx:
    cur = tx.cursor(subdb)
    cur.first()
    
    print('Reading block info')
    bar = progressbar.ProgressBar(max_value=progressbar.UnknownLength)
    i = 0
    
    for key, value in cur:
        
        block_id = get_block_id(key)
        
        account = value[:32]
        balance = value[32:48]
        assert len(value[48:]) == 0
        
        account_id = get_account_id(encode_account(account))            
        balance_raw = bin2balance_raw(balance)
        
        block_to_account[block_id] = account_id
        block_to_balance[block_id] = balance_raw
        
        i += 1
        bar.update(i)
        
    bar.finish()
"""

# Process blocks per type

for subdbname in ['change', 'open', 'receive', 'send']:
    
    subdb = env.open_db(subdbname.encode())
    
    with env.begin(write=False) as tx:
        cur = tx.cursor(subdb)
        cur.first()
        
        print('Processing "%s" blocks' % subdbname)
        bar = progressbar.ProgressBar(max_value=progressbar.UnknownLength)
        i = 0        
        
        p = processor_functions[subdbname]
        
        sqlcur.execute('begin')

        for key, value in cur:
            
            p(sqlcur, key, value)
            
            i += 1
            bar.update(i)            
            
        sqlcur.execute('commit')   

        bar.finish()        
        
# Store accounts
        
print('Storing account info')
bar = progressbar.ProgressBar(max_value=progressbar.UnknownLength)
i = 0        
        
sqlcur.execute('begin')

for address, id in account_ids.items():
    
    sqlcur.execute('insert into accounts (id, address) values (?,?)',
        (id, address))
        
    i += 1
    bar.update(i)            
           
sqlcur.execute('commit')

bar.finish()

# Store for each block to which account chain it belongs, can reuse account ids for this.
# This gives a direct mapping from block to chain/account
            