#!/bin/bash
# Demodulate 1200 baud AFSK (FM demodulator) using direwolf
# Thanks to cshields and csete :-)
sox -t ogg $1 -esigned-integer -b 16 -r 48000 -t raw - | direwolf -B 1200 -b 16 -n 1 -r 48000 -q hd -t 0 -q h -q d -d p -d t -a 0 -c ax25_1200.conf -
