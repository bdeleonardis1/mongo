"""Sharded cluster fixture for executing JSTests against."""

import os.path
import time

import pymongo
import pymongo.errors

from buildscripts.resmokelib import config
from buildscripts.resmokelib import core
from buildscripts.resmokelib import errors
from buildscripts.resmokelib import logging
from buildscripts.resmokelib import utils
from buildscripts.resmokelib.multiversionconstants import LAST_LTS_MONGOS_BINARY
from buildscripts.resmokelib.testing.fixtures import interface
from buildscripts.resmokelib.testing.fixtures import replicaset
from buildscripts.resmokelib.testing.fixtures import standalone
from buildscripts.resmokelib.utils import registry


class ShardedClusterFixture(interface.Fixture):  # pylint: disable=too-many-instance-attributes
    """Fixture which provides JSTests with a sharded cluster to run against."""

    _CONFIGSVR_REPLSET_NAME = "config-rs"
    _SHARD_REPLSET_NAME_PREFIX = "shard-rs"

    def __init__(  # pylint: disable=too-many-arguments,too-many-locals
            self, logger, job_num, mongos_executable=None, mongos_options=None, mongod_options=None,
            dbpath_prefix=None, preserve_dbpath=False, num_shards=1, num_rs_nodes_per_shard=1,
            num_mongos=1, enable_sharding=None, enable_balancer=True, enable_autosplit=True,
            auth_options=None, configsvr_options=None, shard_options=None, mixed_bin_versions=None):
        """Initialize ShardedClusterFixture with different options for the cluster processes."""

        print("SHARDED")

        interface.Fixture.__init__(self, logger, job_num, dbpath_prefix=dbpath_prefix)

        if "dbpath" in mongod_options:
            raise ValueError("Cannot specify mongod_options.dbpath")

        self.mongos_executable = mongos_executable
        self.mongos_options = utils.default_if_none(mongos_options, {})
        self.mongod_options = utils.default_if_none(mongod_options, {})
        self.mongod_options["set_parameters"] = mongod_options.get("set_parameters", {}).copy()
        self.mongod_options["set_parameters"]["migrationLockAcquisitionMaxWaitMS"] = \
                mongod_options["set_parameters"].get("migrationLockAcquisitionMaxWaitMS", 30000)
        self.preserve_dbpath = preserve_dbpath
        # Use 'num_shards' and 'num_rs_nodes_per_shard' values from the command line if they exist.
        num_shards_option = config.NUM_SHARDS
        self.num_shards = num_shards if not num_shards_option else num_shards_option
        num_rs_nodes_per_shard_option = config.NUM_REPLSET_NODES
        self.num_rs_nodes_per_shard = num_rs_nodes_per_shard if not num_rs_nodes_per_shard_option else num_rs_nodes_per_shard_option
        self.num_mongos = num_mongos
        self.enable_sharding = utils.default_if_none(enable_sharding, [])
        self.enable_balancer = enable_balancer
        self.enable_autosplit = enable_autosplit
        self.auth_options = auth_options
        self.configsvr_options = utils.default_if_none(configsvr_options, {})
        self.shard_options = utils.default_if_none(shard_options, {})
        self.mixed_bin_versions = utils.default_if_none(mixed_bin_versions,
                                                        config.MIXED_BIN_VERSIONS)
        if self.mixed_bin_versions is not None and num_rs_nodes_per_shard is not None:
            num_mongods = self.num_shards * self.num_rs_nodes_per_shard
            if len(self.mixed_bin_versions) != num_mongods:
                msg = (("The number of binary versions specified: {} do not match the number of"\
                        " nodes in the sharded cluster: {}.")).format(len(self.mixed_bin_versions), num_mongods)
                raise errors.ServerFailure(msg)

        self._dbpath_prefix = os.path.join(self._dbpath_prefix, config.FIXTURE_SUBDIR)

        self.configsvr = None
        self.mongos = []
        self.shards = []

    def pids(self):
        """:return: pids owned by this fixture if any."""
        out = []
        if self.configsvr is not None:
            out.extend(self.configsvr.pids())
        else:
            self.logger.debug(
                'Config server not running when gathering sharded cluster fixture pids.')
        if self.shards is not None:
            for shard in self.shards:
                out.extend(shard.pids())
        else:
            self.logger.debug('No shards when gathering sharded cluster fixture pids.')
        return out

    def setup(self):
        """Set up the sharded cluster."""
        if self.configsvr is None:
            self.configsvr = self._new_configsvr()

        self.configsvr.setup()

        if not self.shards:
            for i in range(self.num_shards):
                if self.num_rs_nodes_per_shard is None:
                    shard = self._new_standalone_shard(i)
                elif isinstance(self.num_rs_nodes_per_shard, int):
                    if self.num_rs_nodes_per_shard <= 0:
                        raise ValueError("num_rs_nodes_per_shard must be a positive integer")
                    shard = self._new_rs_shard(i, self.num_rs_nodes_per_shard)
                else:
                    raise TypeError("num_rs_nodes_per_shard must be an integer or None")
                self.shards.append(shard)

        # Start up each of the shards
        for shard in self.shards:
            shard.setup()

    def await_ready(self):
        """Block until the fixture can be used for testing."""
        # Wait for the config server
        if self.configsvr is not None:
            self.configsvr.await_ready()

        # Wait for each of the shards
        for shard in self.shards:
            shard.await_ready()

        # We call self._new_mongos() and mongos.setup() in self.await_ready() function
        # instead of self.setup() because mongos routers have to connect to a running cluster.
        if not self.mongos:
            for i in range(self.num_mongos):
                mongos = self._new_mongos(i, self.num_mongos)
                self.mongos.append(mongos)

        for mongos in self.mongos:
            # Start up the mongos.
            mongos.setup()

            # Wait for the mongos.
            mongos.await_ready()

        client = self.mongo_client()
        self._auth_to_db(client)

        # Turn off the balancer if it is not meant to be enabled.
        if not self.enable_balancer:
            self.stop_balancer()

        # Turn off autosplit if it is not meant to be enabled.
        if not self.enable_autosplit:
            wc = pymongo.WriteConcern(w="majority", wtimeout=30000)
            coll = client.config.get_collection("settings", write_concern=wc)
            coll.update_one({"_id": "autosplit"}, {"$set": {"enabled": False}}, upsert=True)

        # Inform mongos about each of the shards
        for shard in self.shards:
            self._add_shard(client, shard)

        # Ensure that all CSRS nodes are up to date. This is strictly needed for tests that use
        # multiple mongoses. In those cases, the first mongos initializes the contents of the config
        # database, but without waiting for those writes to replicate to all the config servers then
        # the secondary mongoses risk reading from a stale config server and seeing an empty config
        # database.
        self.configsvr.await_last_op_committed()

        # Enable sharding on each of the specified databases
        for db_name in self.enable_sharding:
            self.logger.info("Enabling sharding for '%s' database...", db_name)
            client.admin.command({"enablesharding": db_name})

        # Ensure that the sessions collection gets auto-sharded by the config server
        if self.configsvr is not None:
            primary = self.configsvr.get_primary().mongo_client()
            primary.admin.command({"refreshLogicalSessionCacheNow": 1})

        for shard in self.shards:
            primary = (shard.mongo_client() if self.num_rs_nodes_per_shard is None else
                       shard.get_primary().mongo_client())
            primary.admin.command({"refreshLogicalSessionCacheNow": 1})

    def _auth_to_db(self, client):
        """Authenticate client for the 'authenticationDatabase'."""
        if self.auth_options is not None:
            auth_db = client[self.auth_options["authenticationDatabase"]]
            auth_db.authenticate(self.auth_options["username"],
                                 password=self.auth_options["password"],
                                 mechanism=self.auth_options["authenticationMechanism"])

    def stop_balancer(self, timeout_ms=60000):
        """Stop the balancer."""
        client = self.mongo_client()
        self._auth_to_db(client)
        client.admin.command({"balancerStop": 1}, maxTimeMS=timeout_ms)
        self.logger.info("Stopped the balancer")

    def start_balancer(self, timeout_ms=60000):
        """Start the balancer."""
        client = self.mongo_client()
        self._auth_to_db(client)
        client.admin.command({"balancerStart": 1}, maxTimeMS=timeout_ms)
        self.logger.info("Started the balancer")

    def _do_teardown(self, mode=None):
        """Shut down the sharded cluster."""
        self.logger.info("Stopping all members of the sharded cluster...")

        running_at_start = self.is_running()
        if not running_at_start:
            self.logger.warning("All members of the sharded cluster were expected to be running, "
                                "but weren't.")

        # If we're killing or aborting to archive data files, stopping the balancer will execute
        # server commands that might lead to on-disk changes from the point of failure.
        if self.enable_balancer and mode not in (interface.TeardownMode.KILL,
                                                 interface.TeardownMode.ABORT):
            self.stop_balancer()

        teardown_handler = interface.FixtureTeardownHandler(self.logger)

        for mongos in self.mongos:
            teardown_handler.teardown(mongos, "mongos", mode=mode)

        for shard in self.shards:
            teardown_handler.teardown(shard, "shard", mode=mode)

        if self.configsvr is not None:
            teardown_handler.teardown(self.configsvr, "config server", mode=mode)

        if teardown_handler.was_successful():
            self.logger.info("Successfully stopped all members of the sharded cluster.")
        else:
            self.logger.error("Stopping the sharded cluster fixture failed.")
            raise errors.ServerFailure(teardown_handler.get_error_message())

    def is_running(self):
        """Return true if all nodes in the cluster are all still operating."""
        return (self.configsvr is not None and self.configsvr.is_running()
                and all(shard.is_running() for shard in self.shards)
                and all(mongos.is_running() for mongos in self.mongos))

    def get_internal_connection_string(self):
        """Return the internal connection string."""
        if self.mongos is None:
            raise ValueError("Must call setup() before calling get_internal_connection_string()")

        return ",".join([mongos.get_internal_connection_string() for mongos in self.mongos])

    def get_driver_connection_url(self):
        """Return the driver connection URL."""
        return "mongodb://" + self.get_internal_connection_string()

    def get_node_info(self):
        """Return a list of dicts of NodeInfo objects."""
        output = []
        for shard in self.shards:
            output += shard.get_node_info()
        for mongos in self.mongos:
            output += mongos.get_node_info()
        return output + self.configsvr.get_node_info()

    def _new_configsvr(self):
        """Return a replicaset.ReplicaSetFixture configured as the config server."""

        shard_logging_prefix = "configsvr"
        mongod_logger = logging.loggers.new_fixture_node_logger(self.__class__.__name__,
                                                                self.job_num, shard_logging_prefix)

        configsvr_options = self.configsvr_options.copy()

        auth_options = configsvr_options.pop("auth_options", self.auth_options)
        preserve_dbpath = configsvr_options.pop("preserve_dbpath", self.preserve_dbpath)
        num_nodes = configsvr_options.pop("num_nodes", 1)

        replset_config_options = configsvr_options.pop("replset_config_options", {})
        replset_config_options["configsvr"] = True

        print("mongod_options:", self.mongod_options)

        mongod_options = self.mongod_options.copy()
        mongod_options.update(configsvr_options.pop("mongod_options", {}))
        mongod_options["configsvr"] = ""
        mongod_options["dbpath"] = os.path.join(self._dbpath_prefix, "config")
        mongod_options["replSet"] = ShardedClusterFixture._CONFIGSVR_REPLSET_NAME
        mongod_options["storageEngine"] = "wiredTiger"

        return replicaset.ReplicaSetFixture(
            mongod_logger, self.job_num, mongod_options=mongod_options,
            preserve_dbpath=preserve_dbpath, num_nodes=num_nodes, auth_options=auth_options,
            mixed_bin_versions=None, replset_config_options=replset_config_options,
            shard_logging_prefix=shard_logging_prefix, **configsvr_options)

    def _new_rs_shard(self, index, num_rs_nodes_per_shard):
        """Return a replicaset.ReplicaSetFixture configured as a shard in a sharded cluster."""

        shard_logging_prefix = f"shard{index}"
        mongod_logger = logging.loggers.new_fixture_node_logger(self.__class__.__name__,
                                                                self.job_num, shard_logging_prefix)

        shard_options = self.shard_options.copy()

        auth_options = shard_options.pop("auth_options", self.auth_options)
        preserve_dbpath = shard_options.pop("preserve_dbpath", self.preserve_dbpath)

        replset_config_options = shard_options.pop("replset_config_options", {})
        replset_config_options["configsvr"] = False

        mixed_bin_versions = self.mixed_bin_versions
        if mixed_bin_versions is not None:
            start_index = index * num_rs_nodes_per_shard
            mixed_bin_versions = mixed_bin_versions[start_index:start_index +
                                                    num_rs_nodes_per_shard]

        mongod_options = self.mongod_options.copy()
        mongod_options.update(shard_options.pop("mongod_options", {}))
        mongod_options["shardsvr"] = ""
        mongod_options["dbpath"] = os.path.join(self._dbpath_prefix, "shard{}".format(index))
        mongod_options["replSet"] = ShardedClusterFixture._SHARD_REPLSET_NAME_PREFIX + str(index)

        return replicaset.ReplicaSetFixture(
            mongod_logger, self.job_num, mongod_options=mongod_options,
            preserve_dbpath=preserve_dbpath, num_nodes=num_rs_nodes_per_shard,
            auth_options=auth_options, replset_config_options=replset_config_options,
            mixed_bin_versions=mixed_bin_versions, shard_logging_prefix=shard_logging_prefix,
            **shard_options)

    def _new_standalone_shard(self, index):
        """Return a standalone.MongoDFixture configured as a shard in a sharded cluster."""

        mongod_logger = logging.loggers.new_fixture_node_logger(
            self.__class__.__name__, self.job_num, "shard{}".format(index))

        shard_options = self.shard_options.copy()

        preserve_dbpath = shard_options.pop("preserve_dbpath", self.preserve_dbpath)

        mongod_options = self.mongod_options.copy()
        mongod_options.update(shard_options.pop("mongod_options", {}))
        mongod_options["shardsvr"] = ""
        mongod_options["dbpath"] = os.path.join(self._dbpath_prefix, "shard{}".format(index))

        print("Sharded above standalone")
        return standalone.MongoDFixture(mongod_logger, self.job_num, mongod_options=mongod_options,
                                        preserve_dbpath=preserve_dbpath, **shard_options)

    def _new_mongos(self, index, total):
        """
        Return a _MongoSFixture configured to be used as the mongos for a sharded cluster.

        :param index: The index of the current mongos.
        :param total: The total number of mongos routers
        :return: _MongoSFixture
        """

        if total == 1:
            logger_name = "mongos"
        else:
            logger_name = "mongos{}".format(index)

        mongos_logger = logging.loggers.new_fixture_node_logger(self.__class__.__name__,
                                                                self.job_num, logger_name)

        mongos_options = self.mongos_options.copy()
        mongos_options["configdb"] = self.configsvr.get_internal_connection_string()

        # The last-lts binary is currently expected to live in '/data/multiversion', which is
        # part of the PATH.
        mongos_executable = self.mongos_executable if self.mixed_bin_versions is None else LAST_LTS_MONGOS_BINARY

        return _MongoSFixture(mongos_logger, self.job_num, dbpath_prefix=self._dbpath_prefix,
                              mongos_executable=mongos_executable, mongos_options=mongos_options)

    def _add_shard(self, client, shard):
        """
        Add the specified program as a shard by executing the addShard command.

        See https://docs.mongodb.org/manual/reference/command/addShard for more details.
        """

        connection_string = shard.get_internal_connection_string()
        self.logger.info("Adding %s as a shard...", connection_string)
        client.admin.command({"addShard": connection_string})


class _MongoSFixture(interface.Fixture):
    """Fixture which provides JSTests with a mongos to connect to."""

    REGISTERED_NAME = registry.LEAVE_UNREGISTERED  # type: ignore

    # pylint: disable=too-many-arguments
    def __init__(self, logger, job_num, dbpath_prefix, mongos_executable=None, mongos_options=None):
        """Initialize _MongoSFixture."""

        interface.Fixture.__init__(self, logger, job_num)

        # Default to command line options if the YAML configuration is not passed in.
        self.mongos_executable = utils.default_if_none(mongos_executable, config.MONGOS_EXECUTABLE)

        self.mongos_options = utils.default_if_none(mongos_options, {}).copy()

        self.mongos = None
        self.port = None
        self._dbpath_prefix = dbpath_prefix

    def setup(self):
        """Set up the sharded cluster."""
        if "port" not in self.mongos_options:
            self.mongos_options["port"] = core.network.PortAllocator.next_fixture_port(self.job_num)
        self.port = self.mongos_options["port"]

        if config.ALWAYS_USE_LOG_FILES:
            self.mongos_options["logpath"] = self._dbpath_prefix + "/mongos-{port}.log".format(
                port=self.port)
            self.mongos_options["logappend"] = ""

        mongos = core.programs.mongos_program(self.logger, executable=self.mongos_executable,
                                              **self.mongos_options)
        try:
            self.logger.info("Starting mongos on port %d...\n%s", self.port, mongos.as_command())
            mongos.start()
            self.logger.info("mongos started on port %d with pid %d.", self.port, mongos.pid)
        except Exception as err:
            msg = "Failed to start mongos on port {:d}: {}".format(self.port, err)
            self.logger.exception(msg)
            raise errors.ServerFailure(msg)

        self.mongos = mongos

    def pids(self):
        """:return: pids owned by this fixture if any."""
        if self.mongos is not None:
            return [self.mongos.pid]
        else:
            self.logger.debug('Mongos not running when gathering mongos fixture pids.')
        return []

    def await_ready(self):
        """Block until the fixture can be used for testing."""
        deadline = time.time() + standalone.MongoDFixture.AWAIT_READY_TIMEOUT_SECS

        # Wait until the mongos is accepting connections. The retry logic is necessary to support
        # versions of PyMongo <3.0 that immediately raise a ConnectionFailure if a connection cannot
        # be established.
        while True:
            # Check whether the mongos exited for some reason.
            exit_code = self.mongos.poll()
            if exit_code is not None:
                raise errors.ServerFailure("Could not connect to mongos on port {}, process ended"
                                           " unexpectedly with code {}.".format(
                                               self.port, exit_code))

            try:
                # Use a shorter connection timeout to more closely satisfy the requested deadline.
                client = self.mongo_client(timeout_millis=500)
                client.admin.command("ping")
                break
            except pymongo.errors.ConnectionFailure:
                remaining = deadline - time.time()
                if remaining <= 0.0:
                    raise errors.ServerFailure(
                        "Failed to connect to mongos on port {} after {} seconds".format(
                            self.port, standalone.MongoDFixture.AWAIT_READY_TIMEOUT_SECS))

                self.logger.info("Waiting to connect to mongos on port %d.", self.port)
                time.sleep(0.1)  # Wait a little bit before trying again.

        self.logger.info("Successfully contacted the mongos on port %d.", self.port)

    def _do_teardown(self, mode=None):
        if self.mongos is None:
            self.logger.warning("The mongos fixture has not been set up yet.")
            return  # Teardown is still a success even if nothing is running.

        if mode == interface.TeardownMode.ABORT:
            self.logger.info(
                "Attempting to send SIGABRT from resmoke to mongos on port %d with pid %d...",
                self.port, self.mongos.pid)
        else:
            self.logger.info("Stopping mongos on port %d with pid %d...", self.port,
                             self.mongos.pid)
        if not self.is_running():
            exit_code = self.mongos.poll()
            msg = ("mongos on port {:d} was expected to be running, but wasn't. "
                   "Process exited with code {:d}").format(self.port, exit_code)
            self.logger.warning(msg)
            raise errors.ServerFailure(msg)

        self.mongos.stop(mode=mode)
        exit_code = self.mongos.wait()

        # Python's subprocess module returns negative versions of system calls.
        # pylint: disable=invalid-unary-operand-type
        if exit_code == 0 or (mode is not None and exit_code == -(mode.value)):
            self.logger.info("Successfully stopped the mongos on port {:d}".format(self.port))
        else:
            self.logger.warning("Stopped the mongos on port {:d}. "
                                "Process exited with code {:d}.".format(self.port, exit_code))
            raise errors.ServerFailure(
                "mongos on port {:d} with pid {:d} exited with code {:d}".format(
                    self.port, self.mongos.pid, exit_code))

    def is_running(self):
        """Return true if the cluster is still operating."""
        return self.mongos is not None and self.mongos.poll() is None

    def get_internal_connection_string(self):
        """Return the internal connection string."""
        if self.mongos is None:
            raise ValueError("Must call setup() before calling get_internal_connection_string()")

        return "localhost:%d" % self.port

    def get_driver_connection_url(self):
        """Return the driver connection URL."""
        return "mongodb://" + self.get_internal_connection_string()

    def get_node_info(self):
        """Return a list of NodeInfo objects."""
        info = interface.NodeInfo(name=self.logger.name, port=self.port, pid=self.mongos.pid)
        return [info]
