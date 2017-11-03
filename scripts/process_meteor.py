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

# What wildcard string to use when searching for new soft-bit files.
SOURCE_PATH = "/tmp/data*.s"

# Where to place the complete images.
DESTINATION_DIR = "/tmp/.satnogs/data/"
# Where to put the soft-bit files.
RAW_DESTINATION_DIR = "/tmp/.satnogs/data/complete/"

# Locations for temporary files
TEMP_DIR = "/tmp/"
TEMP_FILENAME = "meteor_image_temp"

# Paths to binaries we need. If these binaries are not on $PATH, change the paths below to point to the appropriate place.
MEDET_PATH = "medet_arm"
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


def combine_images():
    """
    Use the 'convert' utility (from imagemagick) to concatenate 
    a set of resultant METEOR images.
    """

    raw_image_path = TEMP_DIR + TEMP_FILENAME + "*.bmp"
    result_image = TEMP_DIR + TEMP_FILENAME + ".png"
    
    # Call convert to try and append the resultant images together.
    subprocess.call([CONVERT_PATH, "-append", raw_image_path, result_image])

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


if __name__ == "__main__":
    # Search for files.
    _input_files = glob(SOURCE_PATH)

    for _file in _input_files:
        # Cleanup any temporary files.
        cleanup_data()

        # Sleep for a bit.
        print("Waiting for %d seconds before processing." % WAIT_TIME)
        sleep(WAIT_TIME)

        # Process file
        print("Attempting to process: %s" % _file)
        run_medet(_file, MEDET_ARGS_COMPOSITE)

        if ENABLE_THERMAL:
            run_medet(TEMP_DIR + TEMP_FILENAME + ".dec", MEDET_ARGS_THERMAL, "_thermal")

        result = combine_images()

        if result != None:
            print("Processing successful!")
            _file_basename = os.path.basename(_file)
            _file_noext = _file_basename.split(".")[0]
            _dest = DESTINATION_DIR + _file_noext + ".png"
            # Move image to data dir, to be upload.
            shutil.move(result, _dest)
            # Move raw data to complete directory.
            shutil.move(_file, RAW_DESTINATION_DIR + os.path.basename(_file))

        else:
            print("Processing Unsuccessful.")
            # Move failed file into complete directory for later cleanup.
            shutil.move(_file, RAW_DESTINATION_DIR + os.path.basename(_file))

        cleanup_data()



