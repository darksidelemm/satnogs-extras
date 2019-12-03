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

# Whether you want to delete input files when complete
DELETE_COMPLETE_FILES = False

# Paths to binaries we need. If these binaries are not on $PATH, change the
# paths below to point to the appropriate place.
MEDET_PATH = DATA_PATH + "/bin/medet_arm"
METEOR_DEMOD_PATH = DATA_PATH + "/bin/meteor_demod"
CONVERT_PATH = "convert"

# NORAD IDs
METEOR_M2_1_ID = 40069
METEOR_M2_2_ID = 44387

# Constants for the color channels, BGR order to match medet output
CH_R = 2
CH_G = 1
CH_B = 0

# Which APIDs to look for
APIDS = {
  CH_R: 68,
  CH_G: 65,
  CH_B: 64
}

# Color mapping to produce false color image
VIS_IMAGE_CHS = {
  CH_R: CH_G,
  CH_G: CH_G,
  CH_B: CH_B}

# Which channel to use for ir image
IR_IMAGE_CH = CH_R

# medet default arguments to produce separate images for each individual channel
MEDET_DEF_ARGS = ['-q', '-s', 
                  '-r', APIDS[CH_R], '-g', APIDS[CH_G], '-b', APIDS[CH_B]]

# medet extra arguments per sat
MEDET_EXTRA_ARGS = {
  METEOR_M2_1_ID: []
  METEOR_M2_2_ID: ['-diff']}

# meteor_demod args to produce an s-file from an iq-file for M2 2
METEOR_DEMOD_ARGS_M2_2 = ['-B', '-R', '1000', '-f', '24', '-b', '300',
                          '-s', '156250', '-r', '72000', '-d', '1000',
                          '-m', 'oqpsk']

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


def convert_images(output_name):
    """
    Use the 'convert' utility (from imagemagick) to convert
    a set of resultant METEOR images.
    """

    fc_file = output_name + "_fc.png"
    ir_file = output_name + "_ir.png"

    convert_cmd_fc = [CONVERT_PATH,
                      "%s_%d.bmp" % (output_name, VIS_IMAGE_CHS[CH_R]),
                      "%s_%d.bmp" % (output_name, VIS_IMAGE_CHS[CH_G]),
                      "%s_%d.bmp" % (output_name, VIS_IMAGE_CHS[CH_B]),
                      "-channel", "RGB", "-combine",
                      fc_file]

    convert_cmd_ir = [CONVERT_PATH,
                      "%s_%d.bmp" % (output_name, IR_IMAGE_CH),
                      ir_file]

    return_code = subprocess.call(convert_cmd_fc)
    print("convert fc returned %d " % return_code)

    return_code = subprocess.call(convert_cmd_ir)
    print("convert ir returned %d " % return_code)

    generated_images = []
    if os.path.isfile(fc_file):
        generated_images.append(fc_file)

    if os.path.isfile(ir_file):
        generated_images.append(ir_file)

    return generated_images


def run_medet(source_file, output_name, extra_args):
    """
    Attempt to run the medet meteor decoder over a file.
    """

    medet_command = [MEDET_PATH, source_file, output_name]
    medet_command.extend(MEDET_DEF_ARGS)
    medet_command.extend(extra_args)
    print(medet_command)
    return_code = subprocess.call(medet_command)

    print("medet returned %d " % return_code)

    return return_code


def generate_s_file(iq_file):
    """
    Attempt to run meteor_demod over an iq file to obtain an s-file
    """

    s_file = os.path.splitext(iq_file)[0] + ".s"
    dem_cmd = [METEOR_DEMOD_PATH]
    dem_cmd.extend(METEOR_DEMOD_ARGS_M2_2)
    dem_cmd.extend(['-o', s_file, iq_file])

    print(dem_cmd)

    with open(os.path.dirname(s_file) + "/" + 'demodulate.log', 'w') as f_out:
        return_code = subprocess.call(dem_cmd, stdout=f_out)

    print("meteor_demod returned %d " % return_code)

    if os.path.isfile(s_file):
        print("meteor_demod produced s file")
    else:
        print("meteor_demod did not produce s file")
        s_file = None

    return s_file


def process_s_file(s_file, sat_id):
    """
    Process an s file and place the generated images in the satnogs data folder
    """

    output_name = os.path.splitext(s_file)[0]

    medet_ret = run_medet(s_file, output_name, MEDET_EXTRA_ARGS[sat_id])

    output_files = []
    if medet_ret == 0:
        output_files = convert_images(output_name)

    if len(output_files) > 0:
        print("Images are created")
        for output_file in output_files:
            shutil.move(output_file, DESTINATION_DIR)
    else:
        print("No images are created")


def handle_complete_file(complete_file, complete_dir):
    """
    Move or delete a file that we are done processing
    """

    if DELETE_COMPLETE_FILES:
        os.remove(complete_file)
    else:
        shutil.move(complete_file, complete_dir)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--id', type=int, required=True)
    parser.add_argument('--tle', nargs='*')
    parser.add_argument('--sat_id', type=int)
    args = parser.parse_args()

    sat_id = None

    if args.tle:
        tle = " ".join(args.tle)
        match = re.search(r"1 (\d*)U", tle)
        if match is not None:
            sat_id = int(match.group(1))

    if args.sat_id:
        sat_id = args.sat_id

    if sat_id is None:
        parser.print_help()
        exit(-1)

    print("Post observation script for sat id: %d" % sat_id)

    # Search for s files.
    s_path = S_NEW_PATH % args.id
    new_s_files = glob(s_path)
    iq_path = IQ_NEW_PATH % args.id
    new_iq_files = glob(iq_path)

    if sat_id == METEOR_M2_1_ID:

        print("METEOR M2 1: looking for %s " % s_path)

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
            process_s_file(found_s_file, sat_id)

            # Move processed s file into complete directory
            handle_complete_file(found_s_file, S_COMPLETE_DIR)

    if sat_id == METEOR_M2_2_ID:

        print("METEOR M2 2: looking for %s " % iq_path)

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
                process_s_file(generated_s_file, sat_id)

                # Move processed iq file into complete directory
                handle_complete_file(found_iq_file, IQ_COMPLETE_DIR)
                handle_complete_file(generated_s_file, IQ_COMPLETE_DIR)
