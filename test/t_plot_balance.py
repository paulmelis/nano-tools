#!/usr/bin/env python3
import sys
from nanodb import NanoDatabase

BG_REP1 = 'xrb_39ymww61tksoddjh1e43mprw5r8uu1318it9z3agm7e6f96kg4ndqg9tuds4'
BG_REP2 = 'xrb_31a51k53fdzam7bhrgi4b67py9o7wp33rec1hi7k6z1wsgh8oagqs7bui9p1'

db = NanoDatabase(sys.argv[1])

account = db.account_from_address(BG_REP2)
print(account)

# only send blocks have an explicit balance
blocks = account.chain('send')
print(len(blocks))


for i, b in enumerate(blocks):
    #if b.type != 'send':
    #    continue

    print(i, b.balance())