#!/bin/bash
#setup autostart and autologin
if [ ! -f ~/.config/autostart/cpufantest.desktop ]; then
    mkdir -p ~/.config/autostart
    touch ~/.config/autostart/cpufantest.desktop
    cat >~/.config/autostart/cpufantest.desktop << EOL
[Desktop Entry]
Type=Application
Exec=sh -c "gnome-terminal ~/cpufantest.sh"
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=cpufantest
EOL
    sudo sed -i -e 's/#  AutomaticLoginEnable = true/AutomaticLoginEnable = true/g' /etc/gdm3/custom.conf
    sudo sed -i -e "s/#  AutomaticLogin = user1/AutomaticLogin = $USER/g" "/etc/gdm3/custom.conf"
    sudo apt update
    sudo apt install lm-sensors
    sudo sensors-detect
fi

#Run tests
REBOOT_DURATION=$(( RANDOM%120+180 )) #random reboot between 3-5 minutes
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
