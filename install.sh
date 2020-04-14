#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

if [ "$1" == "--uninstall" ]; then
	sudo -H pip3 uninstall fiveleds
	sudo rm /usr/local/share/applications/fiveleds.desktop
	sudo rm /usr/local/share/pixmaps/fiveleds.png
else
	echo "Install python-wx..."
	sudo apt install python3-wxgtk4.0

	echo "Install fiveleds package..."
	sudo -H pip3 install .

	echo "Create start menu shortcut..."
	sudo chmod +x ./fiveleds.desktop
	sudo mkdir /usr/local/share/applications &> /dev/null
	sudo cp ./fiveleds.desktop /usr/local/share/applications

	echo "Copy icon..."
	sudo mkdir /usr/local/share/pixmaps &> /dev/null
	sudo cp ./fiveleds.png /usr/local/share/pixmaps
fi
