// @tags: [assumes_unsharded_collection]

coll = db.stress_index;
coll.drop();

const DOC_COUNT = 2000000 // ~ 25 MB
const MAX_CHUNK_SIZE = 100000

var inserted = 0;
while (inserted < DOC_COUNT) {
    var docs = []
    for (let i = 0; i < MAX_CHUNK_SIZE && inserted + docs.length < DOC_COUNT; i++) {
        docs.push({"a": 0});
    }
    coll.insertMany(docs)
    inserted += docs.length;
}

assert.eq(coll.find().count(), DOC_COUNT);

assert.commandFailedWithCode(coll.createIndex({ a: 1 }, { unique: true }), ErrorCodes.DuplicateKey);