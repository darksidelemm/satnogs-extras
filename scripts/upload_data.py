#!/usr/bin/env python
#
# Manual upload of data files to satnogs network.
# Useful while data upload is still in development.
#
# This is intended to be run within a post-observation script.
# Note that you will need to source your .env file before this script will work, i.e.
#
# cd $HOME
# source .env
# python upload_data.py
# 

import logging
import os
from urlparse import urljoin
import requests
from satnogsclient import settings

logger = logging.getLogger('satnogsclient')

def post_data():
    logger.info('Post data started')
    """PUT observation data back to Network API."""
    base_url = urljoin(settings.SATNOGS_NETWORK_API_URL, 'data/')
    headers = {'Authorization': 'Token {0}'.format(settings.SATNOGS_API_TOKEN)}

    for f in os.walk(settings.SATNOGS_OUTPUT_PATH).next()[2]:
        file_path = os.path.join(*[settings.SATNOGS_OUTPUT_PATH, f])
        if (f.startswith('receiving_satnogs') or
                f.startswith('receiving_waterfall') or
                os.stat(file_path).st_size == 0):
            continue
        if f.startswith('data'):
            observation = {'demoddata': open(file_path, 'rb')}
        else:
            logger.debug('Ignore file: {0}', f)
            continue
        if '_' not in f:
            continue
        observation_id = f.split('_')[1]
        logger.info(
            'Trying to PUT observation data for id: {0}'.format(observation_id))
        url = urljoin(base_url, observation_id)
        if not url.endswith('/'):
            url += '/'
        logger.debug('PUT file {0} to network API'.format(f))
        logger.debug('URL: {0}'.format(url))
        logger.debug('Headers: {0}'.format(headers))
        logger.debug('Observation file: {0}'.format(observation))
        response = requests.put(url, headers=headers,
                                files=observation,
                                verify=settings.SATNOGS_VERIFY_SSL,
                                stream=True)
        if response.status_code == 200:
            logger.info('Success: status code 200')
            dst = os.path.join(settings.SATNOGS_COMPLETE_OUTPUT_PATH, f)
        else:
            logger.error('Bad status code: {0}'.format(response.status_code))
            dst = os.path.join(settings.SATNOGS_INCOMPLETE_OUTPUT_PATH, f)
        os.rename(os.path.join(settings.SATNOGS_OUTPUT_PATH, f), dst)

if __name__ == "__main__":
	post_data()