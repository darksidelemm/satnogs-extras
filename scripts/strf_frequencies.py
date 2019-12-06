#!/usr/bin/env python
#
#   Dump frequency data from the SatNOGS DB in strf rfplot compatible format.
#
#   Mark Jessop 2019-12-06
#
#   Example: python strf_frequencies.py --fmin 434e6 --fmax 438e6 >> frequencies.txt
#

import requests
import logging
import argparse


DB_BASE_URL = "https://db.satnogs.org"

def get_active_transmitter_info(fmin, fmax):
    # Open session
    logging.debug("Fetching transmitter information from DB.")
    r = requests.get('{}/api/transmitters'.format(DB_BASE_URL))
    logging.debug("Transmitters received!")

    # Loop
    transmitters = []
    for o in r.json():
        if o["downlink_low"]:
            if o["status"] == "active" and o["downlink_low"] > fmin and o["downlink_low"] <= fmax:
                print("%05d  %.4f" % (o["norad_cat_id"], o["downlink_low"]/1e6))
    logging.debug("Transmitters filtered based on ground station capability.")
    return transmitters


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--fmin', type=float, default=435e6, help="Minimum Frequency (Hz)")
    parser.add_argument('--fmax', type=float, default=438e6, help="Maximum Frequency (Hz)")
    parser.add_argument('-v','--verbose', action='store_true', default=False, help="Debug output.")
    args = parser.parse_args()

    if args.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO


    logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=log_level)
    get_active_transmitter_info(args.fmin, args.fmax)