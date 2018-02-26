import nanodb

db = nanodb.NanoDatabase('/dev/shm/nano.db', trace=True)

bg1 = db.account_from_name('BitGrail Representative 1')
bg2 = db.account_from_name('BitGrail Representative 2')
mctx = db.account_from_name('Mercatox Representative')

print(bg1, bg2)

i = db.account_interactions(bg1, mctx)
print(i)