t = db.jstests_all
t.drop();

t.save({ a: 1 });
assert.eq(t.find().count(), 1);

t.drop();

assert.eq(1, 1);