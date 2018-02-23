#!/usr/bin/env python2
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
def format_amount3(value):
    return "{:,.3f}".format(value)

@app.template_filter('format_amount6')            
def format_amount6(value):
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
        
    res.sort(lambda a,b: cmp(a[2], b[2]))
        
    return render_template('known_accounts.html', accounts=res)

# XXX why is xrb_3jwrszth46rk1mu7rmb4rhm54us8yg1gw3ipodftqtikf5yqdyr7471nsg1k (binance) so slow ?
# does it fetch the whole block chain of 78000 block?
# hmm, kucoin xrb_1niabkx3gbxit5j5yyqcpas71dkffggbr6zpd3heui8rpoocm5xqbdwq44oh is much faster and
# has more blocks (103k)!
@app.route('/account/<id_or_address>')
@app.route('/account/<id_or_address>/<int:block_limit>')
def account(id_or_address, block_limit=100):
    
    db = get_db()
    
    if id_or_address.startswith('xrb_'):
        account = db.account_from_address(id_or_address)
    else:
        id = int(id_or_address)
        account = db.account_from_id(id)
        
    last_blocks = account.chain(limit=block_limit)
    name = account.name()
    
    return render_template('account.html', 
            account=account,
            last_blocks=last_blocks,
            name=name,
            id=account.id)
        
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
