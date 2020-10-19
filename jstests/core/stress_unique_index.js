coll = db.stress_index;
coll.drop();

for (let i = 0; i < 10; i++) {
    coll.save({ "a": 1 });
}

assert.commandFailedWithCode(coll.createIndex({ a: 1 }, { unique: true }), ErrorCodes.DuplicateKey)

assert.eq(coll.find().count(), 10)