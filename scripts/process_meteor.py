#!/usr/bin/env python
#
#   Meteor Decoder Processor
#   Initial version for Metor M2:
#   Mark Jessop <vk5qi@rfhead.net> 2017-09-01
#   Extended for Meteor M2 2:
#   Rico van Genugten @PA3RVG 2019-11-19
#
#   This script processes soft-bit and iq recordings from wherever
#   satnogs_lrpt_demod puts them, then places output images in the satnogs
#   recorded data directory to be uploaded (eventually)
#
#   This script can be directly run as a post observation script, use the
#   following config value in satnogs_setup:
#
#   /path/to/this/script.py --id {{ID}} --tle {{TLE}}
#
#

from glob import glob
import subprocess
import os
import shutil
from time import sleep
import argparse
import re


# main path where all meteor files are. The following subdirs
# are expected: /new_s, /found_s, /complete_s, /new_iq, /found_iq, /complete_iq
DATA_PATH = "/datadrive/meteor"

# Where to place the complete images.
DESTINATION_DIR = "/tmp/.satnogs/data/"

DELETE_COMPLETE_FILES = False

# Paths to binaries we need. If these binaries are not on $PATH, change the
# paths below to point to the appropriate place.
MEDET_PATH = DATA_PATH + "/bin/medet_arm"
METEOR_DEMOD_PATH = DATA_PATH + "/bin/meteor_demod"
CONVERT_PATH = "convert"

METEOR_M2_1_ID = 40069
METEOR_M2_2_ID = 44387

# medet arguments to produce a composite image and also each individual channel
MEDET_ARGS_M2_1 = ['-q', '-S', '-r', '65', '-g', '65', '-b', '64']
MEDET_ARGS_M2_2 = ['-q', '-S', '-r', '65', '-g', '65', '-b', '64',
                   '-int', '-diff']

# Wait for a bit before processing, to avoid clashing with waterfall processing
# and running out of RAM.
WAIT_TIME = 120

# What wildcard string to use when searching for new s and iq files.
S_NEW_PATH = DATA_PATH + "/new_s/data_%d_*.s"
IQ_NEW_PATH = DATA_PATH + "/new_iq/data_%d_*.iq"

# Where to put the s and iq files while processing them.
S_FOUND_DIR = DATA_PATH + "/found_s/"
IQ_FOUND_DIR = DATA_PATH + "/found_iq/"

# Where to put the processed s and iq files.
S_COMPLETE_DIR = DATA_PATH + "/complete_s/"
IQ_COMPLETE_DIR = DATA_PATH + "/complete_iq/"


def convert_images(image_files):
    """
    Use the 'convert' utility (from imagemagick) to convert
    a set of resultant METEOR images.
    """

    output_files = []

    for image_file in image_files:
        # Call convert to convert the image
        output_file = os.path.splitext(image_file)[0] + ".png"
        subprocess.call([CONVERT_PATH, image_file, output_file])

        # See if a resultant image was produced.
        if os.path.isfile(output_file):
            output_files.append(output_file)

    return output_files


def run_medet(source_file, output_name, command_args):
    """
    Attempt to run the medet meteor decoder over a file.
    """

    medet_command = [MEDET_PATH, source_file, output_name].extend(command_args)
    return_code = subprocess.call(medet_command)

    print("medet returned %d " % return_code)

    return return_code


def generate_s_file(iq_file):
    """
    Attempt to run meteor_demod over an iq file to obtain an s-file
    """

    s_file = os.path.splitext(iq_file)[0] + ".s"
    dem_cmd = [METEOR_DEMOD_PATH,
               '-B',
               '-R', '5000',
               '-F', '0.05',
               '-f', '24',
               '-b', '300',
               '-s', '156250',
               '-r', '72000',
               '-m', 'oqpsk',
               '-o', s_file,
               iq_file]

    print(dem_cmd)

    with open(os.path.dirname(s_file) + "/" + 'demodulate.log', 'w') as f_out:
        return_code = subprocess.call(dem_cmd, stdout=f_out)

    print("meteor_demod returned %d " % return_code)

    if os.path.isfile(s_file):
        print("meteor_demod did not produce s file")
        s_file = None
    else:
        print("meteor_demod produced s file")

    return s_file


def process_s_file(s_file, medet_args):
    """
    Process an s file and place the generated images in the satnogs data folder
    """

    output_name = os.path.splitext(s_file)[0]

    run_medet(s_file, output_name, medet_args)

    image_files = glob(output_name + "*.bmp")

    output_files = []
    if len(image_files) > 0:
        print("medet produced output images")
        output_files = convert_images(image_files)
    else:
        print("medet produced no output images.")

    if len(output_files) > 0:
        print("Image conversion successful.")
        for output_file in output_files:
            shutil.move(output_file, DESTINATION_DIR)
    else:
        print("Image conversion unsuccessful.")


def handle_complete_file(complete_file, complete_dir):
    """
    Move or delete a file that we are done processing
    """

    if DELETE_COMPLETE_FILES:
        shutil.move(complete_file, S_COMPLETE_DIR)
    else:
        os.remove(complete_file)


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

    print("Post observation script for sat id: %d" % sat_id)

    # Search for s files.
    new_s_files = glob(S_NEW_PATH % args.id)
    new_iq_files = glob(IQ_NEW_PATH % args.id)

    if sat_id == METEOR_M2_1_ID:

        print("METEOR M2 1: looking for %s " % new_s_files)

    # remove iq files, not needed for M2 1
        for new_iq_file in new_iq_files:
            os.remove(new_iq_file)

        # handle s-files
        for new_s_file in new_s_files:

            print("Processing %s " % new_s_file)

            # move file to found dir so other instances won't process it
            found_s_file = S_FOUND_DIR + os.path.basename(new_s_file)
            shutil.move(new_s_file, found_s_file)

            # Sleep for a bit.
            print("Waiting for %d seconds before processing." % WAIT_TIME)
            sleep(WAIT_TIME)

            # Process soft bit file
            process_s_file(found_s_file, MEDET_ARGS_M2_1)

            # Move processed s file into complete directory
            handle_complete_file(found_s_file, S_COMPLETE_DIR)

    if sat_id == METEOR_M2_2_ID:

        print("METEOR M2 2: looking for %s " % new_iq_files)

        # delete s files, we need to generate a new ones for M2 2
        for new_s_file in new_s_files:
            os.remove(new_s_file)

        # handle iq files
        for new_iq_file in new_iq_files:

            print("Processing %s " % new_iq_file)

            # move file to found dir so other instances won't process it
            found_iq_file = IQ_FOUND_DIR + os.path.basename(new_iq_file)
            shutil.move(new_iq_file, found_iq_file)

            # Sleep for a bit.
            print("Waiting for %d seconds before processing." % WAIT_TIME)
            sleep(WAIT_TIME)

            # Generate s file
            generated_s_file = generate_s_file(found_iq_file)

            # Process s file if there is one
            if generated_s_file is not None:
                process_s_file(generated_s_file, MEDET_ARGS_M2_2)

                # Move processed iq file into complete directory
                handle_complete_file(found_iq_file, IQ_COMPLETE_DIR)
                handle_complete_file(generated_s_file, IQ_COMPLETE_DIR)
