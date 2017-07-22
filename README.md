# Extra Demodulators for SatNOGS
This repository contains extra demodulators and other useful scripts to extend the functionality of a SatNOGS groundstation.

It is assumed that the user has a functional SatNOGS ground station.

## Flowgraphs
* LRPT Demod - Produces a 'wide' (~150 kHz) waterfall, and saves QPSK soft-symbols to /tmp/.satnogs/data/. These can then be demodulated using meteor_decoder (https://github.com/artlav/meteor_decoder)
* BPSK9600 Demod - Demodulates 9600 baud BPSK (ala LilacSat-1) to a 12 kHz IF file, suitable for further processing with gr-satellites. 

## Useful Scripts
* 9600 baud FSK Demodulator Script
  * Requires direwolf and sox be installed.
  * Run using: ./demod_ax25_9k6.sh /path/to/file.ogg