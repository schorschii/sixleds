#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

if [ "$1" == "--uninstall" ]; then
	sudo -H pip3 uninstall sixleds
	sudo rm /usr/share/applications/sixleds.desktop
	sudo rm /usr/share/pixmaps/sixleds.png
	sudo rm /usr/share/pixmaps/sixleds-icon.png
else
	echo "Install python-wx..."
	sudo apt install python3 python3-setuptools python3-wheel python3-distutils python3-pip python3-serial python3-wxgtk4.0

	echo "Install sixleds package..."
	sudo -H pip3 install .

	echo "Create start menu shortcut..."
	sudo chmod +x ./assets/sixleds.desktop
	sudo mkdir /usr/share/applications &> /dev/null
	sudo cp ./assets/sixleds.desktop /usr/share/applications

	echo "Copy icon..."
	sudo mkdir /usr/share/pixmaps &> /dev/null
	sudo cp ./assets/sixleds.png /usr/share/pixmaps
	sudo cp ./assets/sixleds-icon.png /usr/share/pixmaps
fi
