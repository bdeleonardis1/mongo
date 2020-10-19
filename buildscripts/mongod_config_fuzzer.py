"""Command line utility to run resmoke with fuzzed storage configurations"""

import sys
import os
import random
import logging

RESMOKE_COMMAND_BASE = "python3 ./buildscripts/resmoke.py run --mongodSetParameters "

def get_set_parameters(seed):
    """Create random configurations based on the seed"""
    rng = random.Random(seed)
    wt_cursor_cache_size = rng.choices([99, 100])[0]
    return "'{{wiredTigerCursorCacheSize: {0}}}'".format(wt_cursor_cache_size)

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
    seed, provided_params = None, None
    if sys.argv[1] == "--seed":
        seed = int(sys.argv[2])
        provided_params = ' '.join(sys.argv[3:])
    else:
        seed = random.randrange(sys.maxsize)
        provided_params = ' '.join(sys.argv[1:])

    print("Reproducible fuzzresmoke invocation: python buildscripts/fuzzresmoke.py --seed " +
        str(seed) + " " + provided_params)

    os.system(RESMOKE_COMMAND_BASE + get_set_parameters(seed) + " " + provided_params)

main()
