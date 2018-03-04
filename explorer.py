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
from flask import Flask, abort, flash, g, jsonify, redirect, render_template, request, url_for
from jinja2 import evalcontextfilter, Markup

from nanodb import NanoDatabase, KNOWN_ACCOUNTS, BlockNotFound, AccountNotFound
from rainumbers import format_amount

HOST = '127.0.0.1'
PORT = 7777
TRACEDB = False

THOUSAND_SEPARATOR = ','
#THOUSAND_SEPARATOR = '.'
#THOUSAND_SEPARATOR = ' '

DBFILE = sys.argv[1]    

app = Flask(__name__)
app.secret_key = 'doh!'     # XXX should generate this to a separate file

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
    
def adjust_thousand_separator(s):
    # Assumes s has format 1,000,000.00
    if THOUSAND_SEPARATOR == ',':
        return s
    elif THOUSAND_SEPARATOR == '.':
        s = s.replace('.', '#')
        s = s.replace(',', '.')
        s = s.replace('#', ',')
    else:
        s = s.replace(',', ' ')
    return s

@app.template_filter('format_amount2')            
def format_amount_3(amount):
    s = format_amount(amount, 2)
    s = adjust_thousand_separator(s)
    return Markup(s)
    
@app.template_filter('format_amount3')            
def format_amount_3(amount):
    s = format_amount(amount, 3)
    s = adjust_thousand_separator(s)
    return Markup(s)
    
@app.template_filter('format_amount6')            
def format_amount_6(amount):
    s = format_amount(amount, 6)
    s = adjust_thousand_separator(s)
    return Markup(s)

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

@app.route('/account/<id_or_address>')
@app.route('/account/<id_or_address>/<int:block_limit>')
def account(id_or_address, block_limit=100):
    
    db = get_db()
    
    try:
        if id_or_address.startswith('xrb_'):
            account = db.account_from_address(id_or_address)
        else:
            id = int(id_or_address)
            account = db.account_from_id(id)
    except AccountNotFound:
        flash('Account %s not found' % id_or_address)
        return redirect(url_for('known_accounts'))
    except ValueError:
        flash('Invalid account ID "%s", must be integer >= 0' % id_or_address)
        return redirect(url_for('known_accounts'))        
            
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
    
    try:
        if len(id_or_hash) == 64:
            block = db.block_from_hash(id_or_hash)
        else:
            id = int(id_or_hash)
            block = db.block_from_id(id)
    except BlockNotFound:
        flash('Block %s not found' % id_or_hash)
        return redirect(url_for('known_accounts'))
    except ValueError:
        flash('Invalid block ID "%s", must be integer >= 0' % id_or_hash)
        return redirect(url_for('known_accounts'))
        
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
        
        
@app.route('/account_or_block', methods=['POST'])
def account_or_block():
    
    if request.method == 'POST':
        value = request.form['value']
        value = value.strip()
        
        if value.startswith('xrb_'):
            return redirect(url_for('account', id_or_address=value))
        elif len(value) == 64:
            return redirect(url_for('block', id_or_hash=value))
        else:
            flash("Value provided ('%s') doesn't look like account nor block hash" % value)
            return redirect(url_for('known_accounts'))
            
    else:
        abort(405)
            
        
    
if __name__ == '__main__':    
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    
    app.run(host=HOST, port=PORT, debug=True)
