"""Command line utility to run resmoke with fuzzed storage configurations"""

import sys
import os
import random
import argparse

# Get relative imports to work when the package is not installed on the PYTHONPATH.
if __name__ == "__main__" and __package__ is None:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# pylint: disable=wrong-import-position
import buildscripts.resmokelib.cli as cli
from buildscripts.resmokelib import utils

configs = [
    {
        "name": "wiredTigerCursorCacheSize",
        "generate": lambda rng: rng.randint(10, 100)
    },
    {
        "name": "wiredTigerSessionCloseIdleTimeSecs",
        "generate": lambda rng: rng.randint(90, 100)
    }
]

def get_parser():
    """Returns the parser"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--fuzzSeed", help="Allows user to specify a seed to reproduce behavior")
    parser.add_argument("--mongodSetParameters", help="Overrides the fuzzed parameters")

    return parser


def get_reproducible_command(seed, provided_params, args):
    """Returns a string command that includes the seed that users can run to reproduce the
    behavior"""
    if provided_params:
        return "python buildscripts/mongod_config_fuzzer.py --fuzzSeed={0} --mongodSetParameters='{1}' {2}".format(seed, provided_params, ' '.join(args))
    else:
        return "python buildscripts/mongod_config_fuzzer.py --fuzzSeed={0} {1}".format(seed, ' '.join(args))


def get_fuzzed_parameters(seed):
    """Create random configurations based on the seed"""
    rng = random.Random(seed)
    params = {}
    for config in configs:
        params[config["name"]] = config["generate"](rng)

    return params


def merge_parameters(fuzzed_params, provided_params):
    """Returns a dictionary in which the provided params overwrite the fuzzed_params"""
    for key, value in provided_params.items():
        fuzzed_params[key] = value

    return fuzzed_params


def convert_dict_to_unquoted_json(dct):
    """
    Returns a json string with unquoted keys and values. For example if the input is: 
    {"hello": "world"} the output would be "{hello: world}"
    """
    json = ""
    for key, value in dct.items():
        json += "{0}: {1}, ".format(key, value)
    json = json[:-2] # delete ', ' for the last key/value pair

    return "{" + json + "}"


def main():
    """Usage of fuzzresmoke:
    Run fuzzresmoke exactly as you would resmoke, with the following two exceptions:
    1. Leave off the run command (fuzzresmoke has not other commands so we leave it off)
    2. Optionally provide a random seed as the first parameter with --seed. Not that if you provide
    a seed it must be the first parameter.

    For example, to run the all2.js file with random configurations you would run:
    python buildscripts/fuzzresmoke.py --suites=core jstests/core/all2.js 

    To run all2.js with a provided seed, you would run:
    python buildscripts/fuzzresmoke.py --seed 123 --suites=core jstests/core/all2.js 
    """
    known, unknown = get_parser().parse_known_args(sys.argv)
    unknown = unknown[1:] # deletes the "buildscripts/mongod_config_fuzzer.py" from the args list
    
    seed = None
    if not known.fuzzSeed:
        seed = random.randrange(sys.maxsize)
    else:
        seed = int(known.fuzzSeed)

    print("Reproducible mongod_config_fuzzer command:", get_reproducible_command(seed, known.mongodSetParameters, unknown))

    parameters = get_fuzzed_parameters(seed)
    if known.mongodSetParameters:
        parameters = merge_parameters(parameters, utils.load_yaml(known.mongodSetParameters))

    resmoke_args = ["buildscripts/resmoke.py", "run"]
    resmoke_args.append("--mongodSetParameters=" + convert_dict_to_unquoted_json(parameters))
    resmoke_args += unknown # add the rest of the user provided arguments

    cli.main(resmoke_args)

main()
