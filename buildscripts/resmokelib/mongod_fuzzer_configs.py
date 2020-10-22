"""Generator functions for all parameters that we fuzz when invoked with --fuzzMongodConfigs"""

def generate_eviction_configs(rng):
    """Generates random configurations for wiredTigerEngineConfigString parameter"""
    eviction_checkpoint_target = rng.randint(1, 100)
    eviction_target = rng.randint(10, 99)
    eviction_trigger = rng.randint(eviction_target, 100)
    eviction_dirty_target = rng.randint(1, eviction_target)
    eviction_dirty_trigger = rng.randint(1, eviction_dirty_target)

    close_idle_time_secs = rng.randint(1, 100)
    close_handle_minimum = rng.randint(0, 1000)
    close_scan_interval = rng.randint(1, 100)

    return """'eviction_checkpoint_target={0},eviction_dirty_target={1},eviction_dirty_trigger={2},
           eviction_target={3},eviction_trigger={4},file_manager=(close_handle_minimum={5},
           close_idle_time={6},close_scan_interval={7})'""".format(eviction_checkpoint_target,
                                                                  eviction_target,
                                                                  eviction_trigger,
                                                                  eviction_dirty_target,
                                                                  eviction_dirty_trigger,
                                                                  close_idle_time_secs,
                                                                  close_handle_minimum,
                                                                  close_scan_interval)

FUZZER_CONFIGS = [
    {
        "name": "wiredTigerCursorCacheSize",
        "generate": lambda rng: rng.randint(-100, 100)
    },
    {
        "name": "wiredTigerSessionCloseIdleTimeSecs",
        "generate": lambda rng: rng.randint(0, 300)
    },
    {
        "name": "wiredTigerConcurrentWriteTransactions",
        "generate": lambda rng: rng.randint(64, 50 * 1000)
    },
    {
        "name": "wiredTigerConcurrentReadTransactions",
        "generate": lambda rng: rng.randint(64, 50 * 1000)
    },
    # {
    #     "name": "wiredTigerEngineConfigString",
    #     "generate": generate_eviction_configs
    # }
]
