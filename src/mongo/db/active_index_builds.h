/**
 *    Copyright (C) 2018-present MongoDB, Inc.
 *
 *    This program is free software: you can redistribute it and/or modify
 *    it under the terms of the Server Side Public License, version 1,
 *    as published by MongoDB, Inc.
 *
 *    This program is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *    Server Side Public License for more details.
 *
 *    You should have received a copy of the Server Side Public License
 *    along with this program. If not, see
 *    <http://www.mongodb.com/licensing/server-side-public-license>.
 *
 *    As a special exception, the copyright holders give permission to link the
 *    code of portions of this program with the OpenSSL library under certain
 *    conditions as described in each individual source file and distribute
 *    linked combinations including the program with the OpenSSL library. You
 *    must comply with the Server Side Public License in all respects for
 *    all of the code used other than as permitted herein. If you modify file(s)
 *    with this exception, you may extend this exception to your version of the
 *    file(s), but you are not obligated to do so. If you do not wish to do so,
 *    delete this exception statement from your version. If you delete this
 *    exception statement from all source files in the program, then also delete
 *    it in the license file.
 */

#pragma once

#include <map>

#include "mongo/db/catalog/index_builds_manager.h"
#include "mongo/db/repl_index_build_state.h"
#include "mongo/platform/mutex.h"


namespace mongo {

class ActiveIndexBuilds {

public:
    // Checks if _allIndexBuilds is empty without acquiring a lock. Should only be used when
    // it is safe to check if the map is empty without a lock.
    bool unlockedIsEmpty();

    void waitForAllIndexBuildsToStopForShutdown(OperationContext* opCtx);

    void assertNoIndexBuildInProgress() const;

    // TODO: gotta figure out assertNoIndexBuildInProgForCollection and _filter...

    void awaitIndexBuildFinished(OperationContext* opCtx, const UUID& buildUUID);

    void waitUntilAnIndexBuildFinishes(OperationContext* opCtx);

    void sleepIndexBuilds_forTestOnly(bool sleep);

    void verifyNoIndexBuilds_forTestOnly();

    StatusWith<std::shared_ptr<ReplIndexBuildState>> getIndexBuild(const UUID& buildUUID) const;

    void awaitNoIndexBuildInProgressForCollection(OperationContext* opCtx,
                                                  const UUID& collectionUUID,
                                                  IndexBuildProtocol protocol);

    void awaitNoIndexBuildInProgressForCollection(OperationContext* opCtx,
                                                  const UUID& collectionUUID);

    void awaitNoBgOpInProgForDb(OperationContext* opCtx, StringData db);


    /* Originally private, heavily refactored methods */
    void unregisterIndexBuild(IndexBuildsManager* indexBuildsManager,
                              std::shared_ptr<ReplIndexBuildState> replIndexBuildState);

    using IndexBuildFilterFn = std::function<bool(const ReplIndexBuildState& replState)>;
    std::vector<std::shared_ptr<ReplIndexBuildState>> filterIndexBuilds(
        IndexBuildFilterFn indexBuildFilter) const;


private:
    std::vector<std::shared_ptr<ReplIndexBuildState>> _filterIndexBuilds_inlock(
        WithLock lk, IndexBuildFilterFn indexBuildFilter) const;

    mutable Mutex _mutex = MONGO_MAKE_LATCH("IndexBuildsCoordinator::_mutex");

    // Build UUID to index build information
    stdx::unordered_map<UUID, std::shared_ptr<ReplIndexBuildState>, UUID::Hash> _allIndexBuilds;

    // Waiters are notified whenever one of the three maps above has something added or removed.
    stdx::condition_variable _indexBuildsCondVar;

    // Generation counter of completed index builds. Used in conjuction with the condition
    // variable to receive notifications when an index build completes.
    uint32_t _indexBuildsCompletedGen;

    bool _sleepForTest = false;
};
}  // namespace mongo