coll = db.stress_index;
coll.drop();

const DOC_COUNT = 1500000 // ~ 50 MB

for (let i = 0; i < DOC_COUNT; i++) {
    coll.save({ "a": 1 });
}

assert.commandFailedWithCode(coll.createIndex({ a: 1 }, { unique: true }), ErrorCodes.DuplicateKey)