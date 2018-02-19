#!/usr/bin/env python3
# $ python3 -i t_int.py file.db 
# >>> db.call(...)
import sys
from nanodb import NanoDatabase

BG_REP1 = 'xrb_39ymww61tksoddjh1e43mprw5r8uu1318it9z3agm7e6f96kg4ndqg9tuds4'
BG_REP2 = 'xrb_31a51k53fdzam7bhrgi4b67py9o7wp33rec1hi7k6z1wsgh8oagqs7bui9p1'

db = NanoDatabase(sys.argv[1])
