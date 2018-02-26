Nano tools
==========
 
Some Python-based tools for exploring the Nano block-lattice and LMDB-based
database that the Nano wallet and node software at [1] use. 
Nano (https://nano.org) is a cryptocurrency that aims to be feeless, 
instant and high throughput. Note that this project has no relation to 
the official Nano project.

Included is a tool to convert (a subset of) stored blocks to a SQLite database 
for easy querying with SQL. Also includes an explorer similar to the one on 
nano.org, mostly for testing, but also usable to browse the data.

In case you find this software useful, donations are welcome at
xrb_1mycqeczobsiyerohkmeeyt7ehyyfjyz5h4hi53ffb6p5qjrefzfcrpc454t

Paul Melis (paul.melis@gmail.com)

[1] https://github.com/nanocurrency/raiblocks


Files
=====

* `dump_wallet_db.py`
  - Low-level tool to inspect the contents of the LMDB database used by the
    Nano wallet/node software.
* `conv2sqlite.py`
  - Main script to convert the LMDB-based Nano/RaiBlocks database to a SQLite
    database
  - Usage:
    1. **Close the official Nano wallet/node software, so nothing else is
         accessing the LMDB database (which by default is at `~/RaiBlocks`)**.
    2. `$ ./conv2sqlite.py convert`           
       This will create a SQLite database called `nano.db` in the current
       directory. This step will take a couple of minutes for a fully 
       synced Nano wallet/node, also depending on the speed of the disk 
       being written to.
    3. You should now have a SQLite database file `nano.db`
  - Note: the SQLite database is by default written in the current directory.
    You can change the output file with the `-d` option.
  - If you have enough free memory (say 4-8 GBs) you can
    generate the SQLite database on a ram-disk, such as `/dev/shm` on Linux, for
    faster generation and improved query performance. Copy it to a persistent disk 
    later if needed.
* `nanodb.py`
  - A Python module that provides an object-oriented API to the SQLite database
    created by `conv2sqlite.py`. This allows easy querying and navigation
    of blocks, accounts and relations between them. The explorer uses this API.
* `explorer.py`
  - A web-based account and block explorer similar to https://nano.org/en/explore/.
    It lacks certain features and is available mostly to inspect the 
    generated SQLite DB, but can also be used to browse and explore the 
    Nano block-lattice.
  - Usage:
    1. `$ ./explorer.py nano.db`
    2. Browse to http://localhost:7777/known_accounts
* `rainumbers.py`
  - Utility module containing some routines to work with native Nano values, 
    such as accounts, balances and amounts.

Python dependencies:
  - [APSW](https://pypi.python.org/pypi/apsw)
  - [lmdb](https://pypi.python.org/pypi/lmdb) (conv2sqlite.py, dump_wallet_db.py)
  - [numpy](http://www.numpy.org/) (dump_wallet_db.py only)
  - [click](https://pypi.python.org/pypi/click) (conv2sqlite.py only)
  - [Flask](http://flask.pocoo.org/) (explorer.py only)


License
=======

See the LICENSE file in this source distribution.

The included Bootstrap, jQuery and Popper sources (included under
the 'static' directory) have their own license.


Bug reports, feature requests, etc
==================================

Please use https://github.com/paulmelis/nano-tools/issues


FAQ
===

* What operating systems will this work on?
  - In principle it should work everywhere Python and the required dependencies
    are available. In practice, it is developed and tested on Linux. So
    with other operating systems there might be some things not fully working (yet).    

* Why is the code based on Python 3.x?
  - The main reason for using Python 3 was that it comes with an implementation
    of the blake2b hashing algorithm used in Nano, which is used in the routines
    that work on accounts.

* Why convert to a separate SQLite database instead of working directly on
  the LMDB database that the Nano wallet/node software uses?
  1. It is safer to work on a separate copy of the wallet/node database, in case
     anything goes wrong when working with the data.
  2. SQL is a very powerful language for querying. Also, LMDB does not
     offer automatic indexing of the data, leading to potentially slow queries.
  3. An LMDB database only contains key-value pairs, that need to be decoded
     into separate fields. In contrast, a SQL table contains columns, one
     per field, for easier querying.
  4. It is easier and safer to add custom data in a separate table in the
     SQLite database than it is in the LMDB database.

* Is it safe to have the official Nano wallet/node running while converting
  the LMDB database to SQLite?
  - This has not been tested by the author of this software. It is recommended
    that you NOT have the wallet/node running while doing the conversion,
    regardless of what the LMDB docs say about concurrent access. Also, these
    scripts might not handle unexpected changes to the LMDB database well.

* Can I update the database after letting the wallet/node receive new blocks?
  - This is currently not implemented. The only way to update is to rebuild 
    the SQLite database.

* Why use APSW instead of the built-in sqlite3 module?
  - [APSW](http://rogerbinns.github.io/apsw/) is an excellent library, aimed
    at working with SQLite from Python, while sqlite3 follows the DB-API
    which isn't SQLite-specific and somewhat quirky to use.
    The sqlite3 module (depending on your Python version) also has issues with
    transactions in certain scenarios. All in all, APSW is much more pleasant
    to work with. As it is available in many distros as a package or can be
    installed using pip adding it to your system shouldn't be too hard.
