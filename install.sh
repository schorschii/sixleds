#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

if [ "$1" == "--uninstall" ]; then
	sudo -H pip3 uninstall .
	sudo rm /usr/local/share/applications/fiveleds.desktop
else
	sudo -H pip3 install .
	sudo chmod +x ./fiveleds.desktop
	sudo cp ./fiveleds.desktop /usr/local/share/applications
fi
