#!/usr/bin/env python3

"""
Edge notation and meaning: 

    A -> B 

If A must be completed *before* B, i.e. B depends on A
    
    
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

Can you send to the account being sent from?    
"""

MARK_NONE = 0
MARK_TEMPORARY = 1
MARK_PERMATENT = 2

def visit(L, permanent, temporary, nodes, n):

    if n in permanent:
        return
        
    if n in temporary:
        raise ValueError('Not a DAG')
        
    temporary.add(n)
    
    for m in nodes[n]:
        visit(L, permanent, temporary, nodes, m)
        
    temporary.remove(n)
    permanent.add(n)
    
    L.append(n)
    
    
def topological_sort(nodes):
    
    """
    nodes: {<node>: [<target-node>, ...]}
    """
        
    L = []
    
    unmarked = set(nodes.keys())
    permanent = set()
    temporary = set()
    
    while len(unmarked) > 0:        
        n = unmarked.pop()
        visit(L, permanent, temporary, nodes, n)
        
    L.reverse()
        
    return L
    
    
if __name__ == '__main__':
    
    nodes = {
        'A': ['B', 'C', 'D'],
        'B': ['C'],
        'C': [],
        'D': ['B'],
    }
    
    print(topological_sort(nodes))
    
    N = 1000
    
    nodes = {}
    
    for i in range(N):
        deps = 
    