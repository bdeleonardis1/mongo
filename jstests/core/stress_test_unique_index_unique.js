// Tests that unique indexes can be built with a large number of unique values

// @tags: [
//   assumes_unsharded_collection,
//   requires_non_retryable_writes,
// ]

(function() {
"use strict";

load("jstests/core/utils.js");

let coll = db.stress_test_unique_index_unique;
coll.drop();

const kNumDocs = 2000000;  // ~65 MB

loadCollectionWithDocs(coll, kNumDocs, true);

assert.commandWorked(coll.createIndex({a: 1}, {unique: true}));
})();
