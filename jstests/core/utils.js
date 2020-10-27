"use strict";

function loadCollectionWithDocs(collection, numDocs, unique) {
    const kMaxChunkSize = 100000;

    let inserted = 0;
    while (inserted < numDocs) {
        let docs = [];
        for (let i = 0; i < kMaxChunkSize && inserted + docs.length < numDocs; i++) {
            if (unique) {
                docs.push({"a": inserted + i});
            } else {
                docs.push({"a": 0});
            }
        }
        collection.insertMany(docs);
        inserted += docs.length;
    }
}
