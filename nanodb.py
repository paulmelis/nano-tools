#!/usr/bin/env python3
import sys
import apsw

KNOWN_ACCOUNTS = {
    'xrb_3t6k35gi95xu6tergt6p69ck76ogmitsa8mnijtpxm9fkcm736xtoncuohr3': 'Genesis',
    'xrb_13ezf4od79h1tgj9aiu4djzcmmguendtjfuhwfukhuucboua8cpoihmh8byo': 'Landing',
    'xrb_35jjmmmh81kydepzeuf9oec8hzkay7msr6yxagzxpcht7thwa5bus5tomgz9': 'Faucet',
    'xrb_1111111111111111111111111111111111111111111111111111hifc8npp': 'Burn',
    'xrb_3wm37qz19zhei7nzscjcopbrbnnachs4p1gnwo5oroi3qonw6inwgoeuufdp': 'Developer Donations',
    'xrb_1ipx847tk8o46pwxt5qjdbncjqcbwcc1rrmqnkztrfjy5k7z4imsrata9est': 'Developer Fund',
    'xrb_3arg3asgtigae3xckabaaewkx3bzsh7nwz7jkmjos79ihyaxwphhm6qgjps4': 'Official representative #1',
    'xrb_1stofnrxuz3cai7ze75o174bpm7scwj9jn3nxsn8ntzg784jf1gzn1jjdkou': 'Official representative #2',
    'xrb_1q3hqecaw15cjt7thbtxu3pbzr1eihtzzpzxguoc37bj1wc5ffoh7w74gi6p': 'Official representative #3',
    'xrb_3dmtrrws3pocycmbqwawk6xs7446qxa36fcncush4s1pejk16ksbmakis78m': 'Official representative #4',
    'xrb_3hd4ezdgsp15iemx7h81in7xz5tpxi43b6b41zn3qmwiuypankocw3awes5k': 'Official representative #5',
    'xrb_1awsn43we17c1oshdru4azeqjz9wii41dy8npubm4rg11so7dx3jtqgoeahy': 'Official representative #6',
    'xrb_1anrzcuwe64rwxzcco8dkhpyxpi8kd7zsjc1oeimpc3ppca4mrjtwnqposrs': 'Official representative #7',
    'xrb_1hza3f7wiiqa7ig3jczyxj5yo86yegcmqk3criaz838j91sxcckpfhbhhra1': 'Official representative #8',
    'xrb_3wu7h5in34ntmbiremyxtszx7ufgkceb3jx8orkuncyytcxwzrawuf3dy3sh': 'NanoWalletBot',
    'xrb_16k5pimotz9zehjk795wa4qcx54mtusk8hc5mdsjgy57gnhbj3hj6zaib4ic': 'NanoWalletBot representative',
    'xrb_39ymww61tksoddjh1e43mprw5r8uu1318it9z3agm7e6f96kg4ndqg9tuds4': 'BitGrail Representative 1',
    'xrb_31a51k53fdzam7bhrgi4b67py9o7wp33rec1hi7k6z1wsgh8oagqs7bui9p1': 'BitGrail Representative 2',
    'xrb_3decyj8e1kpzrthikh79x6dwhn8ei81grennibmt43mcm9o8fgxqd8t46whj': 'Mercatox Representative',
    'xrb_369dmjiipkuwar1zxxiuixaqq1kfmyp9rwsttksxdbf8zi3qwit1kxiujpdo': 'RaiBlocks Community',
    'xrb_1nanexadj9takfo4ja958st8oasuosi9tf8ur4hwkmh6dtxfugmmii5d8uho': 'Nanex.co Representative',
    'xrb_1niabkx3gbxit5j5yyqcpas71dkffggbr6zpd3heui8rpoocm5xqbdwq44oh': 'KuCoin Representative',
    'xrb_3kab648ixurzeio4ixjowkn89tk3jbwd7sy91i7bnnxynzq13hjrifxpm78c': "Tony's Eliquid Co. Representative",
    'xrb_1tig1rio7iskejqgy6ap75rima35f9mexjazdqqquthmyu48118jiewny7zo': 'OkEx Representative',
    'xrb_1tpzgiiwb69k1rfmpjqc96neca5rgakdajb4azgm6ks8qe1o4gwu4ea575pd': 'TipBot',
    'xrb_3jybgajxebuj9kby3xusmn4sqiomzu15trmkwb1xyrynnc7axss3qp1yn679': 'Nano-Miner',
    'xrb_3jwrszth46rk1mu7rmb4rhm54us8yg1gw3ipodftqtikf5yqdyr7471nsg1k': 'Binance Representative'
}

class NanoDatabase:

    def __init__(self, dbfile, trace=False):
        self.sqldb = apsw.Connection(dbfile, flags=apsw.SQLITE_OPEN_READONLY)
        if trace:
            self.sqldb.setexectrace(self._exectrace)

    def _exectrace(self, cursor, sql, bindings):
        print('%s [%s]' % (sql, repr(bindings)))
        return True

    def close(self):
        # Mostly for use under Flask
        self.sqldb.close()

    def account_from_id(self, id):
        assert isinstance(id, int)
        return Account(self, id)

    def account_from_address(self, addr):
        cur = self.sqldb.cursor()
        try:
            cur.execute('select id from accounts where address=?', (addr,))
            row = next(cur)
            return Account(self, row[0], addr)
        except StopIteration:
            raise ValueError('Unknown account')

    def accounts(self):
        """Return a list of all accounts"""
        res = []
        cur = self.sqldb.cursor()
        cur.execute('select id, address from accounts')
        for id, addr in cur:
            res.append(Account(self, id, addr))
        return res

    def block_from_id(self, id, type=None):
        assert isinstance(id, int)
        return Block(self, id, type)

    def block_from_hash(self, hash):
        cur = self.sqldb.cursor()
        try:
            cur.execute('select id from blocks where hash=?', (hash,))
            row = next(cur)
            return Block(self, int(row[0]))
        except StopIteration:
            raise ValueError('No block with hash %s found' % hash)

    # XXX add blocks()?

    def check(self):
        """Perform consistency checks, mostly for debugging purposes"""

        pass

        # Check for missing blocks, e.g. previous id points to non-existent block

        # Check for accounts not having an open block
        # Check that no forks exist, i.e. two or more blocks with a common previous block

        # Number of send blocks >= number of receive blocks + number of open blocks

        # Check successor value against previous of successor block

        # check block hash length (which are not the same, have leading zeroes?)


    def stats(self):
        pass

        # number of frontiers, i.e. blocks with null next?

    def cursor(self):
        """For when you know what you're doing..."""
        return self.sqldb.cursor()


class Account:

    def __init__(self, db, id, address=None):
        self.db = db
        self.sqldb = db.sqldb
        self.id = id
        if address is None:
            cur = self.db.cursor()
            cur.execute('select address from accounts where id=?', (id,))
            address = next(cur)[0]
        self.address = address
        self.open_block = None
        self.name_ = None

    def __repr__(self):
        return '<Account #%d %s>' % (self.id, self.address)

    # XXX rename to open_block()
    def first_block(self):
        """Should always return an "open" block"""
        if self.open_block is not None:
            return self.open_block
        cur = self.db.cursor()
        cur.execute('select id from blocks where account=? and type=?', (self.id, 'open'))
        try:
            row = next(cur)
        except StopIteration:
            return None
        self.open_block = Block(self.db, row[0])
        return self.open_block

    def chain(self, type=None, limit=None):
        """
        Return all blocks in the chain, in sequence, open block first.
        If "type" is set, only blocks of the requested type will be returned.
        If "limit" is set, at most limit blocks will be returned.
        """

        # XXX how to include not pocketed blocks to this account?
        #     i.e. only send from other account to here, e.g
        #     https://nano.org/en/explore/block/D7C6604C37F23F05D4A98A365DB5B91EFFBEAD3E851EC4A49F579BBB8E88CFF1
        # Or multiple not pocketed ones:
        # https://nano.org/en/explore/account/xrb_39ymww61tksoddjh1e43mprw5r8uu1318it9z3agm7e6f96kg4ndqg9tuds4

        q = 'select block from block_info where account=?'
        v = [self.id]
        if type is not None:
            q += ' and type=?'
            v.append(type)
        q += ' order by sequence desc'
        if limit is not None:
            q += ' limit ?'
            v.append(limit)

        res = []
        cur = self.db.cursor()
        cur.execute(q, v)

        for row in cur:
            b = Block(self.db, row[0])
            res.append(b)

        return res

    def name(self):
        if self.name_ is not None:
            return self.name_
        cur = self.db.cursor()
        cur.execute('select name from accounts where id=?', (self.id,))
        name = next(cur)[0]
        self.name_ = name
        return name

    # def balance()
    # find last send/receive block


class Block:

    def __init__(self, db, id, type=None):
        assert isinstance(id, int)
        self.db = db
        self.sqldb = db.sqldb

        self.id = id
        if type is None:
            cur = self.sqldb.cursor()
            cur.execute('select type from blocks where id=?', (self.id,))
            type = next(cur)[0]
        self.type = type
        self.hash_ = None
        self.balance_ = None
        self.account_ = None
        self.sequence_ = None
        self.destination_ = None

    def __repr__(self):
        return '<Block #%d %s %s>' % (self.id, self.type, self.hash())

    def hash(self):
        if self.hash_ is not None:
            return self.hash_
        cur = self.sqldb.cursor()
        cur.execute('select hash from blocks where id=?', (self.id,))
        self.hash_ = next(cur)[0]
        return self.hash_

    def previous(self):
        """Return the previous block in the chain. Returns None if there is no previous block"""
        cur = self.sqldb.cursor()

        try:
            cur.execute('select previous from blocks where id=?', (self.id,))
            previd = next(cur)[0]
            if previd is None:
                return None
        except StopIteration:
            return None

        cur.execute('select type from blocks where id=?', (previd,))
        prevtype = next(cur)[0]
        return Block(self.db, previd, prevtype)

    def next(self):
        """Return the next block in the chain. Returns None if there is no next block"""
        cur = self.sqldb.cursor()

        try:
            cur.execute('select next from blocks where id=?', (self.id,))
            nextid = next(cur)[0]
            if nextid is None:
                return None
        except StopIteration:
            return None

        cur.execute('select type from blocks where id=?', (nextid,))
        nexttype = next(cur)[0]
        return Block(self.db, nextid, nexttype)

    def other(self):
        """
        Return the "sister block" for certain types of blocks:
        - For a send block return the corresponding receive/open block
        - For a receive/open block return the source block
        """
        if self.type in ['receive', 'open']:
            cur = self.sqldb.cursor()
            try:
                cur.execute('select source from blocks where id=?', (self.id,))
                b = Block(self.db, next(cur)[0])
                assert b.type == 'send'
                return b
            except StopIteration:
                # No source block. E.g. block 991CF190094C00F0B68E2E5F75F6BEE95A2E0BD93CEAA4A6734DB9F19B728948 on genesis account
                return None
        elif self.type == 'send':
            cur = self.sqldb.cursor()
            try:
                cur.execute('select r.id, r.type from blocks s, blocks r where r.source==s.id and s.id=?', (self.id,))
                id, type = next(cur)
                assert type in ['open', 'receive']
                b = Block(self.db, id, type)
                return b
            except StopIteration:
                # No destination block, i.e. not pocketed
                return None

        raise ValueError('Block type should be send, receive or open')

    def account(self):
        if self.account_ is not None:
            return self.account_
        cur = self.sqldb.cursor()
        cur.execute('select account from block_info where block=?', (self.id,))
        id = next(cur)[0]
        self.account_ = self.db.account_from_id(id)
        return self.account_

    # XXX rename to index()?
    def sequence(self):
        """Sequence number of this block in the account chain (open block=0)"""
        if self.sequence_ is not None:
            return self.sequence_
        cur = self.sqldb.cursor()
        cur.execute('select sequence from block_info where block=?', (self.id,))
        idx = next(cur)[0]
        self.sequence_ = idx
        return idx

    def destination(self):
        """For a send block return destination account.
        For other block types return None"""
        if self.type != 'send':
            return None
        if self.destination_ is not None:
            return self.destination_
        cur = self.sqldb.cursor()
        cur.execute('select destination from blocks where id=?', (self.id,))
        destid = next(cur)[0]
        self.destination_ = self.db.account_from_id(destid)
        return self.destination_

    # XXX this needs more work
    def balance(self):
        """
        Return the account balance at this block in the chain
        """
        if self.balance_ is not None:
            return self.self.balance_
            
        if self.type == 'send':
            cur = self.sqldb.cursor()
            cur.execute('select balance from blocks where id=?', (self.id,))
            self.balance_ = next(cur)[0]
        elif self.type in ['receive', 'open']:
            # XXX no no no!
            self.balance_ = self.other().balance()
        else:
            # XXX
            return None

        return self.balance_

    # XXX add balance_raw()

    def amount(self):
        """For a send/receive/open block compute the amount being transfered"""
        if self.type not in ['open', 'send', 'receive']:
            raise TypeError('Not a send/receive/open block')
        if self.type == 'send':
            # Find
            pass


if __name__ == '__main__':

    db = NanoDatabase(sys.argv[1])
    db.check()
