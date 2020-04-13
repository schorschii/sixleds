#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

if [ "$1" == "--uninstall" ]; then
	sudo -H pip3 uninstall fiveleds
	sudo rm /usr/local/share/applications/fiveleds.desktop
else
	sudo apt install python3-wxgtk4.0
	sudo -H pip3 install .
	sudo chmod +x ./fiveleds.desktop
	echo "Create start menu shortcut..."
	sudo mkdir /usr/local/share/applications &> /dev/null
	sudo cp ./fiveleds.desktop /usr/local/share/applications
fi
