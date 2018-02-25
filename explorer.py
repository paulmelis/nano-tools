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

import sys
from flask import Flask, g, jsonify, render_template
from jinja2 import evalcontextfilter, Markup

from nanodb import NanoDatabase, KNOWN_ACCOUNTS

HOST = '127.0.0.1'
PORT = 7777
TRACEDB = False

DBFILE = sys.argv[1]    

app = Flask(__name__)

# Custom filters

@app.template_filter('account_name')
def account_name(address):
    if address in KNOWN_ACCOUNTS:
        return KNOWN_ACCOUNTS[address]
    else:
        return ''
        
@app.template_filter('account_link')     
@evalcontextfilter
def account_link(eval_ctx, account, show_address=True):
    name = account.name()
    s = '<a href="/account/%d">' % account.id
    if name is not None:
        if show_address:
            s += '%s (%s)' % (name, account.address)
        else:
            s += name
    else:
        s += account.address
    s += '</a>'
    if eval_ctx.autoescape:
        s = Markup(s)
    return s
    
@app.template_filter('format_amount3')            
def format_amount_mxrb_3(value):
    value = value / 10**30
    return "{:,.3f}".format(value)

@app.template_filter('format_amount6')            
def format_amount_mxrb_6(value):
    value = value / 10**30
    return "{:,.6f}".format(value)

@app.template_filter('format_hash')            
def format_hash(value):
    return value[:8] + '...' + value[-8:]

# Database stuff    
    
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = NanoDatabase(DBFILE, trace=TRACEDB)
    return db
    
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
        
# Pages
    
@app.route("/")
def index():
    return render_template('index.html')

@app.route("/known_accounts")
def known_accounts():
    
    db = get_db()
    cur = db.cursor()
    
    res = []
    
    for address, name in KNOWN_ACCOUNTS.items():
        
        cur.execute('select id from accounts where address=?', (address,))
        account = next(cur)[0]
        
        res.append((account, address, name))
        
    res.sort(key=lambda v: v[2])
        
    return render_template('known_accounts.html', accounts=res)

# XXX why is xrb_3jwrszth46rk1mu7rmb4rhm54us8yg1gw3ipodftqtikf5yqdyr7471nsg1k (binance) so slow ?
# does it fetch the whole block chain of 78000 block?
# hmm, kucoin xrb_1niabkx3gbxit5j5yyqcpas71dkffggbr6zpd3heui8rpoocm5xqbdwq44oh is much faster and
# has more blocks (103k)!
# it's not the chain() call, probably resolving all the amounts and balances.
# will get better when we compute this in preprocessing
# YYY add list of unpocketed sends to the account

# balance still incorrect? 
# http://localhost:7777/account/xrb_3jwrszth46rk1mu7rmb4rhm54us8yg1gw3ipodftqtikf5yqdyr7471nsg1k
# http://localhost:7777/block/1977214 (1D54C237...144976F2)
# gives exception
@app.route('/account/<id_or_address>')
@app.route('/account/<id_or_address>/<int:block_limit>')
def account(id_or_address, block_limit=50):
    
    db = get_db()
    
    if id_or_address.startswith('xrb_'):
        account = db.account_from_address(id_or_address)
    else:
        id = int(id_or_address)
        account = db.account_from_id(id)
        
    # XXX handle case where there's more blocks than the limit
    last_blocks = account.chain(limit=block_limit, reverse=True)
    unpocketed_blocks = account.unpocketed(limit=block_limit, reverse=True)
    have_transactions = (len(last_blocks) + len(unpocketed_blocks)) > 0
    
    return render_template('account.html', 
            account=account,
            last_blocks=last_blocks,
            unpocketed_blocks=unpocketed_blocks,
            have_transactions=have_transactions,
            num_blocks=account.chain_length())
            
@app.route('/block/<id_or_hash>')
def block(id_or_hash):
    
    db = get_db()
    
    if len(id_or_hash) == 64:
        block = db.block_from_hash(id_or_hash)
    else:
        id = int(id_or_hash)
        block = db.block_from_id(id)
    
    account = block.account()
    global_index = block.global_index()
    chain_index = block.chain_index()
    previous = block.previous()
    next = block.next()
    
    return render_template('block.html', 
            block=block,
            account=account,
            global_index=global_index,
            chain_index=chain_index,
            previous=previous,
            next=next,
            id=block.id)
        
    
if __name__ == '__main__':    
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    
    app.run(host=HOST, port=PORT, debug=True)
