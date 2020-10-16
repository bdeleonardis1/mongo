import sys
import os

def get_set_parameters():
    return "\"{enableTestCommands: 0}\""

os.system("python3 ./buildscripts/resmoke.py run --mongodSetParameters " + get_set_parameters() + " " + ' '.join(sys.argv[1:]))
