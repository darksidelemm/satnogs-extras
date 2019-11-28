#!/usr/bin/env python
#
#   Meteor Decoder Processor
#   Mark Jessop <vk5qi@rfhead.net> 2017-09-01
#
#   This script processes soft-bit recordings from wherever satnogs_lrpt_demod puts them,
#   then places them in the satnogs recorded data directory to be uploaded (eventually)
#
#   It is suggested that this script is run with a post-observation script, 
#   with some kind of locking to avoid multiple instances running. i.e:
#   flock -n /tmp/meteor_process.lock -c "python /path/to/process_meteor.py"
#
from glob import glob
import subprocess
import os
import shutil
from time import sleep
import argparse
import re

# What wildcard string to use when searching for new soft-bit files.
SOURCE_PATH = "/datadrive/meteor/new_s/data_%d_*.s"

# Where to place the complete images.
DESTINATION_DIR = "/tmp/.satnogs/data/"
# Where to put the soft-bit files while processing them.
RAW_INTERMEDIATE_DIR = "/datadrive/meteor/found_s/"
# Where to put the soft-bit files.
RAW_DESTINATION_DIR = "/datadrive/meteor/complete_s/"

# Locations for temporary files
TEMP_DIR = "/datadrive/meteor/tmp/"
TEMP_FILENAME = "meteor_image_temp"

METEOR_M2_1_ID = 40069
METEOR_M2_2_ID = 44387

# Paths to binaries we need. If these binaries are not on $PATH, change the paths below to point to the appropriate place.
MEDET_PATH = "/datadrive/meteor/bin/medet_arm"
CONVERT_PATH = "convert"

# medet arguments to produce a composite image, and also each individual channel.
MEDET_ARGS_COMPOSITE = ['-q', '-cd', '-r', '65', '-g', '65', '-b', '64']
MEDET_ARGS_THERMAL = ['-q', '-d', '-r', '68', '-g', '68', '-b', '68']

# Wait for a bit before processing, to avoid clashing with waterfall processing and running out of RAM.
WAIT_TIME = 120

# Enable Thermal IR output. This requires a second pass over the output file
ENABLE_THERMAL = True


def cleanup_data(source_file = None):
    """
    Cleanup any temporary files we have created, and optionally the source file.
    """

    # Find temporary files.
    _temp_files = glob(TEMP_DIR + TEMP_FILENAME + "*")
    # Delete them.
    for _file in _temp_files:
        os.remove(_file)

    # Delete the source soft-bit file if we have been passed it.
    if source_file != None:
        os.remove(source_file)


def convert_image(suffix = ""):
    """
    Use the 'convert' utility (from imagemagick) to convert
    a set of resultant METEOR images.
    """

    raw_image_path = TEMP_DIR + TEMP_FILENAME + suffix + ".bmp"
    result_image = TEMP_DIR + TEMP_FILENAME + suffix + ".png"

    # Call convert to convert the image
    subprocess.call([CONVERT_PATH, raw_image_path, result_image])

    # See if a resultant image was produced.
    if os.path.isfile(result_image):
        return result_image
    else:
        return None


def run_medet(source_file, command_args, suffix = ""):
    """
    Attempt to run the medet meteor decoder over a file.
    """

    _medet_command = [MEDET_PATH, source_file, TEMP_DIR + TEMP_FILENAME + suffix]
    for _arg in command_args:
        _medet_command.append(_arg)

    ret_code = subprocess.call(_medet_command)

    return ret_code

def process_s_file(s_file):

        # Cleanup any temporary files.
        cleanup_data()

        # Process file
        print("Attempting to process: %s" % s_file)
        run_medet(s_file, MEDET_ARGS_COMPOSITE, "_vis")
        result_vis = convert_image("_vis")

        result_ir = None
        if ENABLE_THERMAL:
            run_medet(TEMP_DIR + TEMP_FILENAME + "_vis.dec", MEDET_ARGS_THERMAL, "_ir")
            result_ir = convert_image("_ir")

        s_file_basename = os.path.basename(s_file)
        s_file_noext = s_file_basename.split(".")[0]
        _dest_vis = DESTINATION_DIR + s_file_noext + "_vis.png"
        _dest_ir  = DESTINATION_DIR + s_file_noext + "_ir.png"

        if result_vis != None:
            print("VIS processing successful!")
            shutil.move(result_vis, _dest_vis)
        else:
            print("VIS Processing unsuccessful.")

        if result_ir != None:
            print("IR processing successful!")
            shutil.move(result_ir, _dest_ir)
        else:
            print("IR Processing unsuccessful.")

        # Move file processed file into complete directory
        shutil.move(s_file, RAW_DESTINATION_DIR + os.path.basename(s_file))

        cleanup_data()

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--id', type=int)
    parser.add_argument('--tle', nargs='*')
    args = parser.parse_args()

    tle = " ".join(args.tle)
    match = re.search(r"1 (\d*)U", tle)
    sat_id = 0
    if match is not None:
        sat_id = int(match.group(1))

    print "sat id: %d" % sat_id

    if sat_id == METEOR_M2_1_ID:

        # Search for files.
        _input_files = glob(SOURCE_PATH % args.id)

        print "METEOR M2 1: looking for %s " % SOURCE_PATH % args.id

        for _found_file in _input_files:

            print "processing %s " % _found_file

            # move file to intermediate dir so other instances won't process it
            _file = RAW_INTERMEDIATE_DIR + os.path.basename(_found_file)
            shutil.move(_found_file, _file)

            # Sleep for a bit.
            print("Waiting for %d seconds before processing." % WAIT_TIME)
            sleep(WAIT_TIME)


            process_s_file(_file)

    if sat_id == METEOR_M2_2_ID:

        print "METEOR M2 2: To be implemented"

