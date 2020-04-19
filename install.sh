#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

if [ "$1" == "--uninstall" ]; then
	sudo -H pip3 uninstall sixleds
	sudo rm /usr/local/share/applications/sixleds.desktop
	sudo rm /usr/local/share/pixmaps/sixleds.png
else
	echo "Install python-wx..."
	sudo apt install python3-wxgtk4.0

	echo "Install sixleds package..."
	sudo -H pip3 install .

	echo "Create start menu shortcut..."
	sudo chmod +x ./assets/sixleds.desktop
	sudo mkdir /usr/local/share/applications &> /dev/null
	sudo cp ./assets/sixleds.desktop /usr/local/share/applications

	echo "Copy icon..."
	sudo mkdir /usr/local/share/pixmaps &> /dev/null
	sudo cp ./assets/sixleds.png /usr/local/share/pixmaps
fi
