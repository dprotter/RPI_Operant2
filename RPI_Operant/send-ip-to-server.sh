#!/bin/bash

# send-ip-to-server

# VARIABLES
USERNAME=pi
SERVER_NAME="mcdb70.colorado.edu"
PI_PATH="/home/pi/uploads/"

sleep 30

ip -4 -br addr | grep UP | awk '{print $3}' | awk -F"/" '{print $1}' > IP-$( hostname -s ).txt
echo "$( date )" >> IP-$( hostname -s ).txt
scp IP-$( hostname -s ).txt "${USERNAME}@${SERVER_NAME}":"${PI_PATH}".
rm IP-$( hostname -s ).txt

exit 0