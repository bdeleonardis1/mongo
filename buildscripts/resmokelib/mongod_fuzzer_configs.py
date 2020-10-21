"""Generator functions for all parameters that we fuzz when invoked with --fuzzMongodConfigs"""

FUZZER_CONFIGS = [
    {
        "name": "wiredTigerCursorCacheSize",
        "generate": lambda rng: rng.randint(10, 100)
    },
    {
        "name": "wiredTigerSessionCloseIdleTimeSecs",
        "generate": lambda rng: rng.randint(90, 100)
    }
]
