import random

class Failpoint(object):
    def __init__(self, failpoint):
        self.failpoint = failpoint
        self.mode = 'alwaysOn'
        self.data = {}

    def to_set_parameter(self):
        return '''--setParameter failpoint.{}={{mode:'{}',data:{}}}'''.format(self.failpoint, self.mode, self.data)

class MongoDConfiguration(object):
    def __init__(self):
        self.wt_cursor_cache_size = 100
        self.wt_session_close_idle_time_secs = 100
        self.wt_close_handle_minimum = 100
        self.wt_close_idle_time_secs = 100
        self.wt_close_scan_interval_secs = 10
        self.wt_concurrent_writers = 100
        self.wt_concurrent_readers = 200
        self.wt_eviction_checkpoint_target = 1
        self.wt_eviction_target = 80
        self.wt_eviction_trigger = 95
        self.wt_eviction_dirty_target = 5
        self.wt_eviction_dirty_trigger = 20

        self.flow_control_enabled = True
        self.flow_control_override = False
        self.flow_control_target_lag_secs = 10
        self.flow_control_threshold_lag_percentage = 0.5
        self.flow_control_max_samples = 10000
        self.flow_control_sample_period = 1000
        self.flow_control_min_tickets_per_second = 100

    def to_list(self):
        return self.__dict__.items()

    def get_set_parameters(self):
        """
        Returns a list of key/value pairs that can be concatenated without escaping to a sequence
        of `--setParameter key=value` strings.
        """
        set_parameters = {
            'wt_cursor_cache_size': 'wiredTigerCursorCacheSize',
            'wt_session_close_idle_time_secs': 'wiredTigerSessionCloseIdleTimeSecs',
            'wt_concurrent_writers': 'wiredTigerConcurrentWriteTransactions',
            'wt_concurrent_readers': 'wiredTigerConcurrentReadTransactions',
            'flow_control_enabled': 'enableFlowControl',
            'flow_control_target_lag_secs': 'flowControlTargetLagSeconds',
            'flow_control_threshold_lag_percentage': 'flowControlThresholdLagPercentage',
            'flow_control_max_samples': 'flowControlMaxSamples',
            'flow_control_sample_period': 'flowControlSamplePeriod',
            'flow_control_min_tickets_per_second': 'flowControlMinTicketsPerSecond',
        }
        failpoints = {
            'flow_control_override': Failpoint("flowControlTicketOverride"),
        }

        ret = []
        for key, value in set_parameters.items():
            ret.append('--setParameter {}={}'.format(
                set_parameters[key], str(self.__dict__[key]).lower()))

        for key, fp_obj in failpoints.items():
            cfg_value = self.__dict__[key]
            if not cfg_value:
                continue

            fp_obj.mode = 'alwaysOn'
            if cfg_value != True: # Is not a boolean, add a `data` object to the failpoint.
                fp_obj.data = cfg_value

            ret.append(fp_obj.to_set_parameter())

        return ' '.join(ret)

    def get_wt_config_string(self):
        eviction_items = [
            ('eviction_checkpoint_target', self.wt_eviction_checkpoint_target),
            ('eviction_dirty_target', self.wt_eviction_dirty_target),
            ('eviction_dirty_trigger', self.wt_eviction_dirty_trigger),
            ('eviction_target', self.wt_eviction_target),
            ('eviction_trigger', self.wt_eviction_trigger),
        ]
        dhandle_items = [
            ('close_handle_minimum', self.wt_close_handle_minimum),
            ('close_idle_time', self.wt_close_idle_time_secs),
            ('close_scan_interval', self.wt_close_scan_interval_secs),
        ]

        str_func = lambda items: ','.join(['{}={}'.format(key, value) for key, value in items])
        return """{},file_manager=({})""".format(
            str_func(eviction_items), str_func(dhandle_items))

    def get_shell_config(self):
        return """--setParameter enableTestCommands=1 {} --wiredTigerEngineConfigString={}""".format(
            self.get_set_parameters(), self.get_wt_config_string())

def generate_cursor_cache_size(config):
    strategy = random.choice(['mongodb', 'none', 'wiredtiger'])
    if strategy == 'mongodb':
        config.wt_cursor_cache_size = random.randint(1, 1000)
    elif strategy == 'none':
        config.wt_cursor_cache_size = 0
    elif strategy == 'wiredtiger':
        config.wt_cursor_cache_size = random.randint(-1000, -1)

def generate_handle_close(config):
    config.wt_close_idle_time_secs = random.randint(1, 1000)
    config.wt_close_handle_minimum = random.randint(0, 1000)
    config.wt_close_scan_interval_secs = random.randint(1, 100)

def generate_eviction(config):
    config.wt_eviction_checkpoint_target = random.randint(1, 100)
    config.wt_eviction_target = random.randint(10, 99)
    config.wt_eviction_trigger = random.randint(config.wt_eviction_target, 100)
    config.wt_eviction_dirty_target = random.randint(1, config.wt_eviction_target)
    config.wt_eviction_dirty_trigger = random.randint(1, config.wt_eviction_dirty_target)

def generate_flow_control(config):
    config.flow_control_enabled = random.choice([True, False])
    if config.flow_control_enabled == False:
        return

    config.flow_control_override = random.choice(
        [lambda: {"numTickets": random.randint(100, 1000*1000)}, lambda: False])()
    if config.flow_control_override:
        return

    config.flow_control_target_lag_secs = random.randint(1, 1000)
    config.flow_control_threshold_lag_percentage = random.random()
    config.flow_control_max_samples = random.randint(1, 1000*1000)
    config.flow_control_sample_period = random.randint(1, 1000*1000)
    config.flow_control_min_tickets_per_second = random.randint(1, 10*1000)

def generate_concurrent_wt_tickets(config):
    config.wt_concurrent_writers = random.randint(64, 50 * 1000)
    config.wt_concurrent_readers = random.randint(64, 50 * 1000)

config = MongoDConfiguration()
for rule in [generate_cursor_cache_size,
             generate_handle_close,
             generate_eviction,
             generate_flow_control,
             generate_concurrent_wt_tickets]:
    rule(config)

print(config.get_shell_config())