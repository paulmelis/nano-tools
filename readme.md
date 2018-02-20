Nano tools
==========

Some Python-based tools for inspecting the Nano/RaiBlocks LMDB database,
including a tool to convert (a subset of) stored blocks to a SQLite database
for easier querying with SQL. Also includes an explorer similar to
the one on nano.org, mostly for testing, but also usable to browse the data.

Paul Melis (paul.melis@gmail.com)

In case you find this software useful, donations are welcome at xrb_1mycqeczobsiyerohkmeeyt7ehyyfjyz5h4hi53ffb6p5qjrefzfcrpc454t


Files
=====

* `dump_wallet_db.py`
  - Low-level tool to inspect the contents of the LMDB database
* `conv2sqlite.py`
  - Main script to convert the LMDB-based Nano/RaiBlocks database to a SQLite
    database
  - Usage:
    1. `$ ./conv2sqlite.py create`       
    2. `$ ./conv2sqlite.py create_indices`
    3. `$ ./conv2sqlite.py derive_block_info`
    4. You should now have a SQLite database file `nano.db`
  - Note: the SQLite database is by default written in the current directory
* `nanodb.py`
  - An Python module that provides an object-oriented API to the SQLite database
    created by `conv2sqlite.py`
* `explorer.py`
  - A web-based account and block explorer similar to https://nano.org/en/explore/.
    Is it not nearly as good-looking, though, and lacks certain features. It was
    added mostly to inspect the generated SQLite DB, but can also be used to browse
    and explore the Nano block-lattice.
  - Usage:
    1. `$ ./explorer.py nano.db`
    2. Browse to http://localhost:7777/known_accounts
* `rainumbers.py`
  - Utility module containing some routines to work with native Nano values, such
    as accounts and balances

Python dependencies:
  - [APSW](https://pypi.python.org/pypi/apsw)
  - [lmdb](https://pypi.python.org/pypi/lmdb) (conv2sqlite.py, dump_wallet_db.py)
  - [numpy](http://www.numpy.org/) (dump_wallet_db.py only)
  - [click](https://pypi.python.org/pypi/click) (conv2sqlite.py only)
  - [progressbar](https://pypi.python.org/pypi/progressbar) (conv2sqlite.py only)
  - [Flask](http://flask.pocoo.org/) (explorer.py only)


License
=======

See the LICENSE file in this source distribution.


Bug reports, feature requests, etc
==================================

Please use https://github.com/paulmelis/nano-tools/issues


FAQ
===

* What operating systems will this work on?
  - In principle it should work everywhere Python and the required dependencies
    are available. In practice, it is developed and tested mostly on Linux. So
    with other operating systems there might be some things not fully working (yet).    

* Why is the code for Python 3.x only?
  - The main reason for using Python 3 was that it comes with an implementation
    of the blake2b hashing algorithm used in Nano, which is used in the routines
    that work on accounts.    

* Why use APSW instead of the built-in sqlite3 module?
  - [APSW](http://rogerbinns.github.io/apsw/) is an excellent library, aimed
    at working with SQLite from Python, while sqlite3 follows the DB-API
    which isn't SQLite-specific and somewhat quirky to use.
    The sqlite3 module (depending on your Python version) also has issues with
    transactions in certain scenarios. All in all, APSW is much more pleasant
    to work with. As it is available in many distros as package or can be
    installed using pip adding it to your system shouldn't be too hard.
