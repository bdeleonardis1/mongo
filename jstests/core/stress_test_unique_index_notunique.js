// Tests that unique indexes can be built with a large number of non-unique values

// @tags: [
//   assumes_unsharded_collection,
//   requires_non_retryable_writes,
// ]

(function() {
"use strict";

load("jstests/core/utils.js");

let coll = db.stress_test_unique_index_notunique;
coll.drop();

const kNumDocs = 2000000;  // ~65 MB

loadCollectionWithDocs(coll, kNumDocs, false);

assert.commandFailedWithCode(coll.createIndex({a: 1}, {unique: true}), ErrorCodes.DuplicateKey);
})();
