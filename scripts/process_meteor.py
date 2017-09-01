#!/usr/bin/env python
#
#	Meteor Decoder Processor
#	Mark Jessop <vk5qi@rfhead.net> 2017-09-01
#
#	This script processes soft-bit recordings from wherever satnogs_lrpt_demod puts them,
# 	then places them in the satnogs recorded data directory to be uploaded (eventually)
#
#	It is suggested that this script is run with a post-observation script.
#
from glob import glob
import subprocess
import os
import shutil

# What wildcard string to use when searching for new soft-bit files.
SOURCE_PATH = "/tmp/data*.s"

# Where to place the complete images.
DESTINATION_DIR = "/tmp/.satnogs/data/"
RAW_DESTINATION_DIR = "/tmp/.satnogs/data/complete/"

# Locations for temporary files
TEMP_DIR = "/tmp/"
TEMP_FILENAME = "meteor_image_temp"

# Paths to binaries we need. If these binaries are not on $PATH, change the paths below to point to the appropriate place.
MEDET_PATH = "medet_arm"
CONVERT_PATH = "convert"

# medet arguments to produce a composite image, and also each individual channel.
MEDET_ARGS = ['-q', '-S', '-r', '66', '-g', '65', '-b', '64']



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

def run_medet(source_file):
	"""
	Attempt to run the medet meteor decoder over a file.
	"""

	_medet_command = [MEDET_PATH, source_file, TEMP_DIR + TEMP_FILENAME]
	for _arg in MEDET_ARGS:
		_medet_command.append(_arg)

	ret_code = subprocess.call(_medet_command)

	return ret_code

if __name__ == "__main__":
	# Search for files.
	_input_files = glob(SOURCE_PATH)

	for _file in _input_files:
		# Cleanup any temporary files.
		cleanup_data()

		# Process file
		print("Attempting to process: %s" % _file)
		run_medet(_file)

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

		cleanup_data()



