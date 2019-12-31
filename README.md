# fiveleds - LED Display Library

A library to control the LED display in the 57North Hackerpspace

----

This ws made for the Maplin N00GA - using the AM004 - 03128/03127 LED Display communication board. It also works with the Velleman MML16CN, MML16R, MML24CN.

This fiveleds object will hold an array of display lines and pages, and an array of Schedules which can be pushed to the device.

An on disk backup will be loaded at creation and stored after every change,

## Functionality

Each line setup by the display can have multiple pages controlled buy the fiveleds.updateline Function.

Each active Schedule will used the cycle the display on each line.
