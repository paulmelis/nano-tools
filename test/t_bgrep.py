#!/usr/bin/env python3
import sys
from nanodb import NanoDatabase

BG_REP1 = 'xrb_39ymww61tksoddjh1e43mprw5r8uu1318it9z3agm7e6f96kg4ndqg9tuds4'
BG_REP2 = 'xrb_31a51k53fdzam7bhrgi4b67py9o7wp33rec1hi7k6z1wsgh8oagqs7bui9p1'

TX_DEC = '870E346AB08AC27A4B6413323BA129654783835DE9132FC0BF7ACE0D22273625'
TX_JAN = '6F107D3093E59D2144C57C4CE950D15E10FBCBF04B1082D24C0FEFD6768177D5'

db = NanoDatabase(sys.argv[1])

b = db.block_from_hash('E08605062351A7CB749D1CD373391A96B46772F406BC005E7472E60DB68DE20F')
print(b)
print(b.other())

bg_rep1 = db.account_from_address(BG_REP1)
bg_rep2 = db.account_from_address(BG_REP2)

print(bg_rep1, bg_rep2)
print(bg_rep1)
print(bg_rep1.first_block())

# Get all blocks in the BG1 rep chain
bg_rep1_chain = bg_rep1.chain()
bg_rep1_blockids = set([b.id for b in bg_rep1_chain])

# Find send from BG(2) to our account
cur = db.cursor()
cur.execute('select s.id, s.type from blocks s, blocks r where r.hash=? and r.source = s.id', (TX_DEC,))
id, type = next(cur)

BG2_JAN = db.block_from_id(id, type)
print('BG2_JAN', BG2_JAN)
print('BG2_JAN.other()', BG2_JAN.other())
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
            b = db.block_from_id(otherid)
            print(b)
            break
    except StopIteration:
        pass
    
    # Get previous block in BG2 chain
    curblock_bg2 = curblock_bg2.previous()
    
    
    