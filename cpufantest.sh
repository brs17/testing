#!/bin/bash

REBOOT_DURATION=$(( RANDOM%180+180 )) #random reboot between 3-5 minutes
FAN_SPEED="`sensors | grep "CPU fan" | awk '{print $3 "\t"}'`"
if [ "$FAN_SPEED" -eq 0 ]
then
    echo "Fan is not spinning"
    echo "Awaiting manual intervention"
    while true; do
        `read -n 1 -s -r -p "Press any key to continue" key`
        if [$key -eq ""]
        then
            echo ""; break;
        fi
    done
else
    echo "Fan is spinning"
fi
echo "Will reboot in $(( REBOOT_DURATION/60 )) minutes and \
$(( REBOOT_DURATION%60 )) seconds."

`sleep $REBOOT_DURATION`
`reboot`
echo "Reboot time!"
