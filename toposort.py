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

import collections
import apsw
import progressbar

"""
Edge notation and meaning: 

    A -> B 

A must be completed *before* B, i.e. B depends on A. This conventation
stays close the idea of a chain of blocks (A -> B -> C -> ...) and its
meaning w.r.t dependency.
    
    
Open block on account B
-----------------------

A(send block) "destination [account]" -> B(open block) "source [block]"
C(open block)                         -> B(open block) "representative [account]"
    
(B.account == account being opened; no dependency)

Example: 8F02D66117CAC96AD0C66DB2DD583F8452D1CCE979FAEA5C72E4937F33F4ADA4
(receive 7M XRB on Developer Fund account from Genesis account)

Open block for developer fund (xrb_1ipx847tk8o46pwxt5qjdbncjqcbwcc1rrmqnkztrfjy5k7z4imsrata9est)

{
    "type": "open",
    "source": "4270F4FB3A820FE81827065F967A9589DF5CA860443F812D21ECE964AC359E05",
    "representative": "xrb_1awsn43we17c1oshdru4azeqjz9wii41dy8npubm4rg11so7dx3jtqgoeahy",
    "account": "xrb_1ipx847tk8o46pwxt5qjdbncjqcbwcc1rrmqnkztrfjy5k7z4imsrata9est",
    "work": "12d10d44912c9085",
    "signature": "712DF7C4AF0BD92446EC64D3F61D54510A93A591A638DB9DE812D9CB1B0B47EDAD31E7B23ECF3FD8AB9A948162A0CB5C1B8AB29E0C672029F53135F6B933B804"
}


Send block on account A
-----------------------

A(?)                                  -> A(send block) "previous [block]"
A(send block) "destination [account]" -> B(receive block) "source [block]"
A(send block) "destination [account]" -> B(open block) 

Example: C1319915AF94196644762318084B22A3AED1F4260281D3DB58E04D6662959E43

Send 300000000 xrb from xrb_1ipx847tk8o46pwxt5qjdbncjqcbwcc1rrmqnkztrfjy5k7z4imsrata9est
                   to xrb_1w76dejea4z9yywhgw477tppf6y5ya8rnxeao1e4qd3yy67w8o71cts6pqzd

{
    "type": "send",
    "previous": "B6C468ED59789B7533DAAB4CCD1A3D71C7A367550F93A3B3AB5AD988E00BA5CC",
    "destination": "xrb_1w76dejea4z9yywhgw477tppf6y5ya8rnxeao1e4qd3yy67w8o71cts6pqzd",
    "balance": "047A63D4920ACDE4D2D99CC540000000",
    "work": "de85d4cf59145ab0",
    "signature": "F95E2A60344A5D63AC62A4B53067D4A96B3AB39EEB5D948F786703C441971CCEEC9224D1E9602CB1B4A1131C439322ECA06513AC80E163980396E2318738BC05"
}

Balance (previous block):   047A729F1A5291F763E06B4840000000
Balance (this block):       047A63D4920ACDE4D2D99CC540000000

>>> int('047A729F1A5291F763E06B4840000000',16) - int('047A63D4920ACDE4D2D99CC540000000',16)
300000000000000000000000000000000L



Receive block on account B
--------------------------

B(previous block)   -> B(receive block) "previous [block]"
A(send block)       -> B(receive block) "source [block]"
Optional:
    A(send block) "destination [account]" -> B(open block)

Example: EE14DE802A996D061D75C6F970C317A5D2871D86E3BEC3A067B4C13F65D2CBCC

Corresponding receive block from send example above.

{
    "type": "receive",
    "previous": "9D6087001AE6E6614096CFE502DCAFBEFDC1BDD50288FC19AB06BBBA6FF125C8",
    "source": "C1319915AF94196644762318084B22A3AED1F4260281D3DB58E04D6662959E43",
    "work": "6b83b4582c089df7",
    "signature": "0A887F607AAF2B60FE6DA5DEA9BF3D9E7BD8FA1DF918471052FC0CBECE6AF7BE861C668ADA79BA46D791DCEDA297BD1876DEA10D2069F332509ACFA43D1E2700"
}



Change block on account B
-------------------------

B(?)            -> B(change block) "previous [block]"
C(open block)   -> B(change block) "representative [account]"

Example: E4F6E1C784A2D516441A919CC4A620CAB6887319BCD186DC637FC5EDA233EF94

{
    "type": "change",
    "previous": "C1319915AF94196644762318084B22A3AED1F4260281D3DB58E04D6662959E43",
    "representative": "xrb_1stofnrxuz3cai7ze75o174bpm7scwj9jn3nxsn8ntzg784jf1gzn1jjdkou",
    "work": "5a267240b70a9f22",
    "signature": "0F36816875BAB31C46BCEE32D3E4A0C3C1B6ED9644CB070E45DFF215E7973E74C7825D9786B71BA397C99F241F63497473D7DF92EA63DD23C371D1271AABAF03"
}



Should A.destination depend on the open block of the account being sent to?
I guess not, as the account might not be opened yet. For example, the last send 
from the genesis account of the remaining funds to the burn account 
(ECCB8CB65CD3106EDA8CE9AA893FEAD497A91BCA903890CBD7A5C59F06AB9113) is never 
received, and the burn hasn't been opened. 
The burn account (xrb_1111111111111111111111111111111111111111111111111111hifc8npp)
is valid though, while the example from the RPC validate_account_number call
(xrb_3e3j5tkog48pnny9dmfzj1r16pg8t1e76dz5tmac6iq689wyjfpi00000000) is invalid.
So in case the send destination account is opened, the send should come
before the destination account's open block.
Same remark for setting a representative to a non-opened account.

Can you send to the account being sent from? Yes!
https://nano.org/en/explore/block/2D6A9F3B01D0BF5973D7482F314362F9BA59E9E8415989EF3D6F574BF73210A2
{
    "type": "send",
    "previous": "514D68178C9B54F03D7F5CABBFC8CEB9F80007BDB6F79E02D46A03132484029B",
    "destination": "xrb_3m8n5i1yprf19mjiqook36eirpyf7er5mabdfaneixtt8fygewn7z7w88sym",
    "balance": "0026B610ABD328978FD07ADA00000000",
    "work": "ef1e40d7cb893a56",
    "signature": "3FC763A6DC0A194F308BEE693F6FCA865A427557E3F993E1A236FF118951F7F4A04E0B2F441BAB63D5A1D34B1D1AD735CCB03036C78EF47277714FBBC1EA8409"
}


"""

def _check(edges):
    """Check consistency"""
    res = True
    for src, dsts in edges.items():
        for dst in dsts:
            if dst not in edges:        
                print('Warning: edges[%d] contains %d, which is not in edges[]' % (src, dst))
                res = False
    return res


def topological_sort(edges):
    
    """
    edges: {<node>: [<target-node>, ...]}
    
    Returns a list of node IDs in (a) topological order.
    """
    
    MARK_UNVISITED = 0
    MARK_TEMPORARY = 1  # Visited (but not all children visited yet)
    MARK_PERMANENT = 2  # Node and all its reachable children visited 

    status = {}   
    for src in edges.keys():
        status[src] = MARK_UNVISITED
        
    L = collections.deque()
    stack = []        
        
    # Push the Genesis block
    stack.append(0)    
    
    # Uses nice trick from http://sergebg.blogspot.nl/2014/11/non-recursive-dfs-topological-sort.html
    while True:
        
        try:            
            n = stack.pop()
                    
            if n >= 0:
                # First time we visit this node
                
                st = status[n]
                
                if st == MARK_PERMANENT:
                    continue
                    
                if st == MARK_TEMPORARY:
                    print(edges[n])
                    raise ValueError('Not a DAG (%d is marked as temporary)' % n)     

                status[n] = MARK_TEMPORARY                    
                
                # Push the current node again, but as a negative value so
                # we know with the corresponding pop later that all children have
                # been visited.
                stack.append(-n-1)
                
                # For all edges from n -> m, push a visit to m
                stack.extend(edges[n])
                
            else:
                # Second time for this node, all its children have been visited
                n = -n-1
                assert status[n] == MARK_TEMPORARY
                status[n] = MARK_PERMANENT
                
                L.appendleft(n)
                
        except IndexError:
            # Stack emtpy, all done!
            break
                        
    # Check that we visited all nodes (which must be true as 
    # everything should be reachable from the genesis block)
    for n in status:
        if status[n] != MARK_PERMANENT:
            print('%d: status %d' % (n, status[n]))
        
    return list(L)
    

def add_edge(edges, src, dst):
    try:
        edges[src].append(dst)
    except KeyError:
        edges[src] = [dst]
            
    
def generate_block_dependencies(cur, account_to_open_block, block_to_account):
    """
    Generate a set of edges that represent dependencies between blocks (and accounts)
    
    Returns a dict:
    - key = block ID
    - value = list of block IDs that depend on the key block
    """
    
    # Process all blocks
        
    edges = {}
    used_block_ids = set()        
    edge_count = 0

    bar = progressbar.ProgressBar('Generating edges')
    
    # XXX include representative?
    cur.execute('select id, type, previous, next, source, destination from blocks')
                
    for id, type, previous, next, source, destination in cur:
        
        this_account = block_to_account[id]
        
        used_block_ids.add(id)
        
        if type == 'open':
            if source is not None:
                # Genesis block (only) has no source, so need the check
                # {other} <source> -> open {this}
                if source != this_account:
                    # Only if not sending to the same account
                    add_edge(edges, source, id)
                    edge_count += 1
                    
            if previous is not None:
                # {other} <previous> -> open {this}
                add_edge(edges, previous, id)
                edge_count += 1
        
        elif type == 'send':
            assert destination is not None
            """
            # XXX we can't make a send block always come after the open
            # block for the account it sends to, as the send may (indirectly) transfer
            # back to the current account and therefore open block. In which case there would be a cycle.
            # The exception is the send block that an open block directly references (in the source field).
            # That case is handled under 'open' above.
            # E.g. cycle starting at 288611994071C94E9881958A29D678974EA26DDD3F75B7D069F8AF82B999FBA8
            # {this} send -> destination account open {other} 
            # Make sure send appears before destination account is opened
            if destination in account_to_open_block:
                if destination != this_account:
                    # Unless sending to same account
                    # XXX Sending to the same account is legal, see 2D6A9F3B01D0BF5973D7482F314362F9BA59E9E8415989EF3D6F574BF73210A2
                    add_edge(edges, id, account_to_open_block[destination])
            """
            
            # {this} send -> receive {other}
            # Handled in receive
            
            # {other} <previous> -> send {this}
            add_edge(edges, previous, id)
            edge_count += 1
            
        elif type == 'receive':
            # {other} send -> receive {this}
            add_edge(edges, source, id)
            
            # {other} <previous> -> receive {this}
            add_edge(edges, previous, id)
            
            edge_count += 2
            
        elif type == 'change':
            # XXX representative
            
            if previous is not None:
                # {other} <previous> -> change {this}
                add_edge(edges, previous, id)
                edge_count += 1
                
        bar.update(edge_count)
                
    # XXX
    for id in used_block_ids:
        if id not in edges:
            edges[id] = []
            
    #_check(edges)
    
    bar.finish()
            
    return edges
     

if __name__ == '__main__':
    
    import sys, time
    
    edges = {
        'A': ['B', 'C', 'D'],
        'B': ['C'],
        'C': [],
        'D': ['B'],
    }
    
    db = apsw.Connection(sys.argv[1], flags=apsw.SQLITE_OPEN_READONLY)
    cur = db.cursor()
    
    # Get open blocks and their accounts
    
    cur.execute('select id, account from blocks where type=?', ('open',))
    
    account_to_open_block = {}
    for id, account in cur:
        account_to_open_block[account] = id

    # Get edges
    
    block_to_account = {}
    cur.execute('select block, account from block_info')
    for block, account in cur:
        block_to_account[block] = account
    
    edges = generate_block_dependencies(cur, account_to_open_block, block_to_account)

    print(len(edges))
    
    print('Sorting')
    t0 = time.time()
    
    order = topological_sort(edges)
    
    t1 = time.time()
    print('done in %.3f s' % (t1-t0))
    