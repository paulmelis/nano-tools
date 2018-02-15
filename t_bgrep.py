#!/usr/bin/env python3
import sys
import apsw

BG_REP1 = 'xrb_39ymww61tksoddjh1e43mprw5r8uu1318it9z3agm7e6f96kg4ndqg9tuds4'
BG_REP2 = 'xrb_31a51k53fdzam7bhrgi4b67py9o7wp33rec1hi7k6z1wsgh8oagqs7bui9p1'

TX_DEC = '870E346AB08AC27A4B6413323BA129654783835DE9132FC0BF7ACE0D22273625'
TX_JAN = '6F107D3093E59D2144C57C4CE950D15E10FBCBF04B1082D24C0FEFD6768177D5'

def blockid2hash(id):
    cur = db.cursor()
    cur.execute('select hash from blocks where id=?', (id,))
    return next(cur)[0]
    
class NanoDatabase:
    
    def __init__(self, dbfile):
        db = apsw.Connection(sys.argv[1], flags=apsw.SQLITE_OPEN_READONLY)
        

class Account:
    
    @classmethod
    def from_address(addr):
        cur = db.cursor()
        cur.execute('select id from accounts where account=?', (addr,))
        row = next(cur)
        if row is None:
            raise ValueError('Unknown account')
        return Account(row[0], addr)

    def __init__(self, id, address=None):
        self.id = id
        if address is None:
            cur = db.cursor()
            cur.execute('select account from accounts where id=?', (id,))
            address = next(cur)[0]
        self.address = address
        self.open_block = None
        
    def __repr__(self):
        return '<Account #%d %s>' % (self.id, self.address)
        
    def first_block(self):
        """Should always return an "open" block"""
        if self.open_block is not None:
            return self.open_block
        cur = db.cursor()
        cur.execute('select id from blocks where account=?', (self.id,))
        self.open_block = Block(next(cur)[0])
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
    
    @staticmethod
    def from_hash(hash):
        cur = db.cursor()
        cur.execute('select id from blocks where hash=?', (hash,))
        row = next(cur)
        if row is None:
            raise ValueError('No block with hash %s found' % hash)
        return Block(int(row[0]))
    
    def __init__(self, id, type=None):
        assert isinstance(id, int)
        self.id = id
        if type is None:
            cur = db.cursor()
            cur.execute('select type from blocks where id=?', (self.id,))
            type = next(cur)[0]
        self.type = type
        self.hash_ = None
        
    def __repr__(self):
        return '<Block #%d %s %s>' % (self.id, self.hash(), self.type)
        
    def hash(self):
        if self.hash_ is not None:
            return self.hash_
        cur = db.cursor()
        cur.execute('select hash from blocks where id=?', (self.id,))
        self.hash_ = next(cur)[0]
        return self.hash_

    def previous(self):
        cur = db.cursor()
        cur.execute('select previous from blocks where id=?', (self.id,))
        previd = next(cur)[0]
        if previd is None:
            return None
        cur.execute('select type from blocks where id=?', (previd,))
        prevtype = next(cur)[0]
        return Block(previd, prevtype)
        
    def next(self):
        cur = db.cursor()
        cur.execute('select next from blocks where id=?', (self.id,))
        nextid = next(cur)[0]
        if nextid is None:
            return None
        cur.execute('select type from blocks where id=?', (nextid,))
        nexttype = next(cur)[0]
        return Block(nextid, nexttype)
        
    def other(self):
        """For a send block return the corresponding receive block,
        for a receive block return the source block"""
        if self.type == 'receive':
            cur = db.cursor()
            cur.execute('select source from blocks where id=?', (self.id,))
            return Block(next(cur)[0])
        elif self.type == 'send':
            cur = db.cursor()
            cur.execute('select r.id, r.type from blocks s, blocks r where r.source==s.id and s.id=?', (self.id,))
            id, type = next(cur)
            return Block(id, type)
        return None


db = apsw.Connection(sys.argv[1], flags=apsw.SQLITE_OPEN_READONLY)

b = Block.from_hash('E08605062351A7CB749D1CD373391A96B46772F406BC005E7472E60DB68DE20F')
print(b)
print(b.other())
doh

bg_rep1 = Account.from_address(BG_REP1)
bg_rep2 = Account.from_address(BG_REP2)

print(bg_rep1, bg_rep2)
print(bg_rep1)
print(bg_rep1.first_block())

cur = db.cursor()

# Get all blocks in the BG1 rep chain
bg_rep1_chain = bg_rep1.chain()
bg_rep1_blockids = set([b.id for b in bg_rep1_chain])


# Find send from BG(2) to our account
cur.execute('select s.id, s.type from blocks s, blocks r where r.hash=? and r.source = s.id', (TX_DEC,))
id, type = next(cur)

BG2_JAN = Block(id, type)
print(BG2_JAN)
print(BG2_JAN.other())
v = BG2_JAN.other().other()
print(v)
    
# Search back in time for a transaction from BG1 to BG2
curblock_bg2 = BG2_JAN
while curblock_bg2 is not None:
    
    # Check current block
    cur.execute(    
        """
        select other.id from blocks bg2, blocks other
        where bg2.type == ? and other.type == ? and bg2.source == other.id
        and bg2.id == ? 
        """,
        ('receive', 'send', curblock_bg2.id)
    )
    
    try:
        row = next(cur)
        otherid = row[0]
        if otherid in bg_rep1_blockids:
            b = Block(otherid)
            print(b)
            break
    except StopIteration:
        pass
    
    # Get previous block in BG2 chain
    curblock_bg2 = curblock_bg2.previous()
    
    
    