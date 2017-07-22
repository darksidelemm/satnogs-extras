#!/bin/bash
# Start Satnogs
cd $HOME
source .env

# Start up dummy rotctld and rigctld instances for satnogs to talk to.
rotctld -m 1 &
rigctld &

# Start satnogs-client, piping all log data to satnogs.log
satnogs-client 2> satnogs.log

# Kill rot/rigctld instances
killall rigctld
killall rotctld