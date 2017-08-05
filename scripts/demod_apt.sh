#!/bin/bash
# Demodulate an APT Recording with wxtoimg
# Mark Jessop 2017-08
sox $1 /tmp/apt_temp.wav rate 11025
wxtoimg -t n -o -S /tmp/apt_temp.wav /tmp/$(basename "$1").png