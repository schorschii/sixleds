# ![sixleds](assets/icons/sixleds-big.png)
**LED Display Control Library, Command Line Utility (CLI) and Graphical User Interface (GUI)**
![Screenshot](.github/screenshot.png)

## Compatibility
This library was made for providing Linux support for the following devices:
- Maplin N00GA - using the AM004-03128/03127 LED Display communication board
- it also works with the Velleman MML16CN, MML16R, MML24CN
- McCrypt LED Light Writing 590996 (the Conrad Laufschrift)

## Package Installation
0. For Windows, you first need to install the driver for the USB-Serial adapter (see `driver` folder). On Linux and macOS, no additional driver is needed.
1. Download and install the `.deb` (recommended) or `.appimage` (for Linux), `.dmg` (for macOS) or `.exe` (for Windows) package from the latest [release on Github](https://github.com/schorschii/sixleds/releases).
2. You can now start the GUI by executing the platform-specific executable. The `.deb` package installs a shortcut to the program in your start menu.
3. (Only on Linux: the `.deb` package also installs the CLI - you can start it with the command `sixleds`.)

## Manual Installation (Linux)
```
cd sixleds
pip3 install .
mkdir /usr/share/pixmaps/sixleds
cp assets/icons/* /usr/share/pixmaps/sixleds
desktop-file-install assets/sixleds.desktop
```

## Contributions Welcome!
I'm happy if you would like to contribute code or sample graphics to this repo. Please open a pull request!

## Functionality
- The sixleds object will hold an array of display lines and pages, and an array of Schedules which can be pushed to the device.
- Each line setup by the display can have multiple pages controlled by the sixleds.updateline Function.
- Each active schedule will used the cycle the display on each line.
- An on disk backup will be loaded at creation and stored after every change.
- Uploading custom graphics to the device is supported. Graphics are saved in simple text files where each char represents one pixel. Char 'A' is used for red, 'D' for green, 'E' for yellow and '@' for no light (LED off). Please check out the examples in `sample-graphics`.

## Quickstart
After installing, you can use it in following ways to send messages to the LED Display.

### The GUI
```
# open the GUI from your start menu or with this command
sixleds-gui
```

### Command Line
```
# the help command will tell you how to use it
sixleds --help

# example: set text "Hello World" to page "A"
# please replace "/dev/ttyUSB0" with the serial port where the device is attached
sixleds --port /dev/ttyUSB0 --set-page A --content "Hello World!"

# example: set page "A" as default run page
sixleds --port /dev/ttyUSB0 --set-default A
```

### Interactive Shell
```
# calling the command line utility without parameters will open the interactive shell
sixleds
```

## Development
### Build Process
```
# macOS
pyinstaller -F --noconsole --icon=assets/icons/sixleds-icon.icns --add-data="assets/icons/sixleds.png:/" --add-data="assets/icons/led-green.png;/" --add-data="assets/icons/led-yellow.png;/" --add-data="assets/icons/led-red.png;/" --add-data="assets/icons/led-off.png;/" sixleds/sixleds-gui

# Windows
pyinstaller -F --noconsole --icon=assets\icons\sixleds-icon.ico --add-data="assets\icons\sixleds.png;/" --add-data="assets\icons\led-green.png;/" --add-data="assets\icons\led-yellow.png;/" --add-data="assets\icons\led-red.png;/" --add-data="assets\icons\led-off.png;/" sixleds\sixleds-gui
```
