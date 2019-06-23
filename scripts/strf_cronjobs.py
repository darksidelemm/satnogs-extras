#!/usr/bin/env python
#
#   SatNOGS STRF Scheduling Helper
#
#   List all upcoming observations for a station as cronjob entries, to help
#   schedule STRF observations.
#
#   Copyright (C) 2019  Mark Jessop <vk5qi@rfhead.net>
#   Released under GNU GPL v3 or later
#
import argparse
import datetime
import logging
import time
import requests
import sys

from dateutil.parser import parse
from dateutil.tz import *


# 40 12 13 2 * /home/pi/satobs/rtl_capture.sh 437.0e6 30m
CRON_DATE = "%M %H %d %m * "
CRON_CMD = "/home/pi/satobs/rtl_capture.sh %d %dm"



def get_upcoming_observations(station_id=1, dev=False):
    ''' Query the SatNOGS network for upcoming scheduled observations for a station,
        and return the rise azimuth of the next pass.

        Args:
            station_id (int): Station ID of the station
            dev (bool): Use network-dev instead of network.

        Returns:
            (list): A list containing one dictionary per upcoming observation.
    '''

    _dev = "-dev" if dev else ""
    _request_url = "https://network%s.satnogs.org/api/observations/?ground_station=%d&vetted_status=unknown" % (_dev, station_id)

    try:
        _r = requests.get(_request_url)
        _obs = _r.json()
    except Exception as e:
        logging.error("Error getting next observation info - %s" % str(e))
        return []

    # The network API returns a list of observation objects.
    if type(_obs) is not list:
        logging.error("SatNOGS API did not return expected list.")
        return []

    # Check that there are actually some observations to look at.
    if len(_obs) == 0:
        logging.info("No scheduled observations found.")
        return []
    
    return _obs



def process_observations(obs_list, observation_length = -1, obs_before = 5):
    for _obs in obs_list:

        _id = _obs['id']
        _norad_id = _obs['norad_cat_id']
        _freq = _obs['transmitter_downlink_low']/1e6

        # Grab start and end-time
        _start_time = parse(_obs['start'])
        _end_time = parse(_obs['end'])
        _length = (_end_time - _start_time).total_seconds() // 60

        logging.debug("Observation %d Start Time: %s" % (_id, _start_time.isoformat()))
        logging.debug("Observation %d Length: %d minutes" % (_id, _length))

        _strf_start = _start_time - datetime.timedelta(0,obs_before*60 + _start_time.second)

        logging.debug("STRF Start Time: %s" % _strf_start.isoformat())

        # Calculate duration of observation, in minutes
        if observation_length == -1:
            _strf_duration = _length + 10
        else:
            _strf_duration = observation_length

        logging.debug("STRF observation Duration: %dm" % _strf_duration)

        # Calculate receive frequency, in Hz. This is set to the nearest 1 MHz boundary above or below
        # the sat frequency.
        _strf_freq = int(round(_freq)*1e6)

        # Generate output cronjob command.
        _cron_cmd = _strf_start.strftime(CRON_DATE) + CRON_CMD % (_strf_freq, _strf_duration)

        _comment = "# Obs ID: %d, NORAD Catalogue ID: %d" % (_id, _norad_id)

        print(_comment)
        print(_cron_cmd)




if __name__ == "__main__":

    # Read in command line arguments.
    parser = argparse.ArgumentParser()
    parser.add_argument('--station-id', type=int, default=-1, help="SatNOGS Station ID")
    parser.add_argument('--network-dev', action='store_true', default=False, help="Use SatNOGS Network-Dev instead of Network.")
    parser.add_argument('--observation-length', default=-1, type=int, help="Observation time in minutes. Defaults to pass duration +/- 5 min")
    parser.add_argument('-v','--verbose', action='store_true', default=False, help="Debug output.")
    args = parser.parse_args()

    if args.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO


    logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=log_level)



    observation_list = get_upcoming_observations(station_id=args.station_id, dev=args.network_dev)

    process_observations(observation_list, observation_length=args.observation_length)











