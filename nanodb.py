#!/usr/bin/env python3
import sys
import apsw

def blockid2hash(id):
    cur = db.cursor()
    cur.execute('select hash from blocks where id=?', (id,))
    return next(cur)[0]
    
class NanoDatabase:
    
    def __init__(self, dbfile):
        self.db = apsw.Connection(dbfile, flags=apsw.SQLITE_OPEN_READONLY)
        
    def account_from_id(self, id):
        assert isinstance(id, int)
        return Account(self.db, id)      
        
    def account_from_address(self, addr):
        cur = self.db.cursor()
        cur.execute('select id from accounts where address=?', (addr,))
        row = next(cur)
        if row is None:
            raise ValueError('Unknown account')
        return Account(self.db, row[0], addr)        
        
    def block_from_id(self, id, type=None):
        assert isinstance(id, int)
        return Block(self.db, id, type)
    
    def block_from_hash(self, hash):
        cur = self.db.cursor()
        cur.execute('select id from blocks where hash=?', (hash,))
        row = next(cur)
        if row is None:
            raise ValueError('No block with hash %s found' % hash)
        return Block(self.db, int(row[0]))
        
    def accounts(self):
        res = []
        cur = self.db.cursor()
        cur.execute('select id, address from accounts')
        for id, addr in cur:
            res.append(Account(self.db, id, addr))
        return res
        
    def cursor(self):
        """For when you know what you're doing..."""
        return self.db.cursor()
        
class Account:

    def __init__(self, db, id, address=None):
        self.db = db
        self.id = id
        if address is None:
            cur = self.db.cursor()
            cur.execute('select address from accounts where id=?', (id,))
            address = next(cur)[0]
        self.address = address
        self.open_block = None
        
    def __repr__(self):
        return '<Account #%d %s>' % (self.id, self.address)
        
    def first_block(self):
        """Should always return an "open" block"""
        if self.open_block is not None:
            return self.open_block
        cur = self.db.cursor()
        cur.execute('select id from blocks where account=?', (self.id,))
        self.open_block = Block(self.db, next(cur)[0])
        return self.open_block
        
    def chain(self):
        """Return all blocks in the chain, open block first"""
        res = []
        b = self.first_block()
        while b is not None:
            res.append(b)
            b = b.next()
        return res


class Block:
    
    def __init__(self, db, id, type=None):
        assert isinstance(id, int)
        self.db = db
        self.id = id
        if type is None:
            cur = self.db.cursor()
            cur.execute('select type from blocks where id=?', (self.id,))
            type = next(cur)[0]
        self.type = type
        self.hash_ = None
        self.balance_ = None
        
    def __repr__(self):
        return '<Block #%d %s %s>' % (self.id, self.hash(), self.type)
        
    def hash(self):
        if self.hash_ is not None:
            return self.hash_
        cur = self.db.cursor()
        cur.execute('select hash from blocks where id=?', (self.id,))
        self.hash_ = next(cur)[0]
        return self.hash_

    def previous(self):
        cur = self.db.cursor()
        cur.execute('select previous from blocks where id=?', (self.id,))
        previd = next(cur)[0]
        if previd is None:
            return None
        cur.execute('select type from blocks where id=?', (previd,))
        prevtype = next(cur)[0]
        return Block(self.db, previd, prevtype)
        
    def next(self):
        cur = self.db.cursor()
        cur.execute('select next from blocks where id=?', (self.id,))
        nextid = next(cur)[0]
        if nextid is None:
            return None
        cur.execute('select type from blocks where id=?', (nextid,))
        nexttype = next(cur)[0]
        return Block(self.db, nextid, nexttype)
        
    def other(self):
        """
        Return the "sister block" for certain types of blocks:
        - For a send block return the corresponding receive/open block
        - For a receive block return the source block
        - For an open block return the source block
        """
        if self.type in ['receive', 'open']:
            cur = self.db.cursor()
            cur.execute('select source from blocks where id=?', (self.id,))
            b = Block(self.db, next(cur)[0])
            assert b.type == 'send'
            return b
        elif self.type == 'send':
            cur = self.db.cursor()
            cur.execute('select r.id, r.type from blocks s, blocks r where r.source==s.id and s.id=?', (self.id,))
            id, type = next(cur)
            assert type in ['open', 'receive']
            b = Block(self.db, id, type)
            return b
        
        raise ValueError('Block type should be send or receive')
        
    def balance(self):
        if self.type != 'send':
            raise ValueError('Block must have type send for balance')
        if self.balance_ is not None:
            return self.self.balance_
        cur = self.db.cursor()
        cur.execute('select balance from blocks where id=?', (self.id,))
        self.balance_ = next(cur)[0]
        return self.balance_
