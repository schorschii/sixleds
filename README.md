# fiveleds - LED Display Control Library

## Compatibility
This library was made for providing Linux support for the following devices:
- Maplin N00GA - using the AM004-03128/03127 LED Display communication board
- it also works with the Velleman MML16CN, MML16R, MML24CN
- McCrypt LED Light Writing 590996 (the Conrad Laufschrift)

## Installation
```
# download and go to package dir
cd fiveleds

# install system-wide
sudo -H pip3 install .

# now you can execute the script
# the help command will tell you how to use the command line utility
fiveleds --help

# calling the binary without parameters will open the interactive shell
fiveleds

# to uninstall use
sudo -H pip3 uninstall fiveleds
```

## Functionality
- The fiveleds object will hold an array of display lines and pages, and an array of Schedules which can be pushed to the device.
- Each line setup by the display can have multiple pages controlled by the fiveleds.updateline Function.
- Each active schedule will used the cycle the display on each line.
- An on disk backup will be loaded at creation and stored after every change.

## Quickstart
After installing, you can send messages to the LED Display by using:
```
# Set text "Hello World" to page "A"
# Please replace "/dev/ttyUSB0" with the serial port where the device is attached
fiveleds --port /dev/ttyUSB0 --set-page A --content "Hello World!"

# Set page "A" as default run page
fiveleds --port /dev/ttyUSB0 --set-default A
```
