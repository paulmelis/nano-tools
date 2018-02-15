#!/usr/bin/env python3
import sys, os, time
from struct import unpack
import lmdb, apsw, numpy
from rainumbers import *

DATADIR = 'RaiBlocks'
DBPREFIX = 'data.ldb'

SCHEMA = """
begin;

drop table if exists accounts;
drop table if exists blocks;

create table blocks (
    id          integer not null,
    hash        text not null,
    type        text not null,
    
    -- All blocks
    previous    integer,            -- Can be NULL for an open block
    next        integer,            -- "successor"
    signature   text not null,
    
    -- Depends on block type
    work            text,           -- change, open, receive, send
    representative  integer,        -- change
    source          integer,        -- open, receive
    destination     integer,        -- send
    balance         text,           -- send             -- type?
    account         integer,        -- open, vote
    sequence_number integer,        -- vote
    --block           text,           -- vote
    
    primary key(id),
    unique(hash)
);

create table accounts (
    id          integer not null,
    account     text not null,      -- xrb_....     -- rename to address?
    
    primary key(id),
    unique(account)
);

commit;
"""

dbfile = sys.argv[1]

sqldb = apsw.Connection(dbfile)
sqlcur = sqldb.cursor()
sqlcur.execute(SCHEMA)

# Map block hash (bytes) to integer ID (starting at 1)
block_ids = {}
next_block_id = 1

# Map account name ('xrb_...') to integer ID (starting at 1)
account_ids = {}
next_account_id = 1

def get_block_id(blockhash):
    
    if bin2hex(blockhash) == '0000000000000000000000000000000000000000000000000000000000000000':
        return None
    
    global next_block_id
    try:
        return block_ids[blockhash]
    except KeyError:
        block_ids[blockhash] = next_block_id
        next_block_id += 1
        return next_block_id-1

def get_account_id(accname):
    
    global next_account_id
    try:
        return account_ids[accname]
    except KeyError:
        account_ids[accname] = next_account_id
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
    
    blockid = get_block_id(key)
    
    sqlcur.execute('insert into blocks (id, hash, type, source, representative, account, signature, work, next) values (?,?,?,?,?,?,?,?,?)',
        (blockid, bin2hex(key), 'open', get_block_id(source_block), get_account_id(encode_account(representative)), get_account_id(encode_account(account)), bin2hex(signature), '%08x' % work, get_block_id(successor)))
  
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
    
    blockid = get_block_id(key)
    
    sqlcur.execute('insert into blocks (id, hash, type, previous, representative, signature, work, next) values (?,?,?,?,?,?,?,?)',
        (blockid, bin2hex(key), 'change', get_block_id(previous_block), get_account_id(encode_account(representative)), bin2hex(signature), '%08x' % work, get_block_id(successor)))

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
    
    blockid = get_block_id(key)
    
    sqlcur.execute('insert into blocks (id, hash, type, previous, source, signature, work, next) values (?,?,?,?,?,?,?,?)',
        (blockid, bin2hex(key), 'receive', get_block_id(previous_block), get_block_id(source_block), bin2hex(signature), '%08x' % work, get_block_id(successor)))

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
    print('... balance %s (%.6f Mxrb)' % (bin2hex(balance), bin2balance(balance)))
    print('... signature %s' % bin2hex(signature))
    print('... work %08x' % work)
    print('... successor %s' % bin2hex(successor))
    """

    blockid = get_block_id(key)
    
    # XXX store balance in what form, Mxrb? or store in string with fixed precision?
    sqlcur.execute('insert into blocks (id, hash, type, previous, destination, balance, signature, work, next) values (?,?,?,?,?,?,?,?,?)',
        (blockid, bin2hex(key), 'send', get_block_id(previous_block), get_account_id(encode_account(destination)), bin2balance(balance), bin2hex(signature), '%08x' % work, get_block_id(successor)))


processor_functions = {
    'change'    : process_change_entry,
    'open'      : process_open_entry,
    'receive'   : process_receive_entry,
    'send'      : process_send_entry,
    #'vote': process_vote_entry,
}

env = lmdb.Environment(
        os.path.join(os.environ['HOME'],DATADIR,DBPREFIX), subdir=False,
        map_size=10*1024*1024*1024, max_dbs=16,
        readonly=True)

for subdbname in ['change', 'open', 'receive', 'send']:
    
    subdb = env.open_db(subdbname.encode())
    
    with env.begin(write=False) as tx:
        cur = tx.cursor(subdb)
        cur.first()
        
        p = processor_functions[subdbname]
        
        sqlcur.execute('begin')

        for key, value in cur:
            p(sqlcur, key, value)
            
        sqlcur.execute('commit')    
        
sqlcur.execute('begin')

for account, id in account_ids.items():
    sqlcur.execute('insert into accounts (id, account) values (?,?)',
        (id, account))

sqlcur.execute('end')

# Store for each block to which account chain it belongs, can reuse account ids for this
            