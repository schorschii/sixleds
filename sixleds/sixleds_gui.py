#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os import path, getcwd
from functools import partial
from PyQt6 import QtWidgets, QtGui, QtCore
import webbrowser
import sixleds
import logging
import time
import platform
import glob
import serial
import sys


class QClickLabel(QtWidgets.QLabel):
    clicked = QtCore.pyqtSignal()

    def mousePressEvent(self, event):
        self.clicked.emit()
        QtWidgets.QLabel.mousePressEvent(self, event)

class SixledsScheduleWindow(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super(SixledsScheduleWindow, self).__init__(parent)
        self.parent = parent
        self.InitUI()

    def InitUI(self):
        self.layout = QtWidgets.QGridLayout()

        self.textPages = QtWidgets.QLineEdit()
        self.textPages.setPlaceholderText("e.g. ABDEF - leave empty to disable this schedule")

        self.textStart = QtWidgets.QLineEdit()
        self.textStart.setPlaceholderText("YYMMDDHHmm")

        self.textEnd = QtWidgets.QLineEdit()
        self.textEnd.setPlaceholderText("YYMMDDHHmm")

        self.comboSchedule = QtWidgets.QComboBox()
        self.comboSchedule.currentTextChanged.connect(self.OnScheduleChanged)
        for schedule, details in self.parent.SCHEDULES.items():
            self.comboSchedule.addItem(schedule)

        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok|QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.accepted.connect(self.OnSend)
        #self.buttonBox.rejected.connect(self.OnClose)

        self.layout.addWidget(QtWidgets.QLabel("Schedule to edit:"), 0, 0)
        self.layout.addWidget(self.comboSchedule, 0, 1)
        self.layout.addWidget(QtWidgets.QLabel("Pages to display:"), 1, 0)
        self.layout.addWidget(self.textPages, 1, 1)
        self.layout.addWidget(QtWidgets.QLabel("Start date/time:"), 2, 0)
        self.layout.addWidget(self.textStart, 2, 1)
        self.layout.addWidget(QtWidgets.QLabel("End date/time:"), 3, 0)
        self.layout.addWidget(self.textEnd, 3, 1)
        self.layout.addWidget(self.buttonBox, 4, 1)

        self.setLayout(self.layout)
        self.setWindowTitle("Schedule Editor")

    def OnScheduleChanged(self, page):
        self.textPages.setText("")
        self.textStart.setText("0001010000")
        self.textEnd.setText("9912302359")
        if(page in self.parent.SCHEDULES.keys() and "pages" in self.parent.SCHEDULES[page]):
            self.textPages.setText(self.parent.SCHEDULES[page]["pages"])
            self.textStart.setText(self.parent.SCHEDULES[page]["start"])
            self.textEnd.setText(self.parent.SCHEDULES[page]["end"])

    def OnSend(self):
        selectedSchedule = self.comboSchedule.currentText()
        if(self.textPages.text() == ""):
            self.parent.ld.updatesched(selectedSchedule, active=False)
        else:
            self.parent.ld.updatesched(selectedSchedule, self.textPages.text().upper(), active=True,
                start=self.textStart.text(),
                end=self.textEnd.text()
            )
        self.parent.ld.pushchanges()
        self.parent.SCHEDULES[selectedSchedule]['pages'] = self.textPages.text()
        self.parent.SCHEDULES[selectedSchedule]['start'] = self.textStart.text()
        self.parent.SCHEDULES[selectedSchedule]['end'] = self.textEnd.text()
        self.close()

class SixledsGraphicWindow(QtWidgets.QMainWindow):
    COLORS = {
        "Off"    : { "code":"@", "pixmap":"led-off.png" },
        "Red"    : { "code":"A", "pixmap":"led-red.png" },
        "Green"  : { "code":"D", "pixmap":"led-green.png" },
        "Yellow" : { "code":"E", "pixmap":"led-yellow.png" }
    }

    ledsHorizontal = 33
    ledsVertical = 8
    ledWidth = 10
    ledHeight = 10

    def __init__(self, parent=None):
        super(SixledsGraphicWindow, self).__init__(parent)
        self.InitUI()

    def InitUI(self):
        buttonOpenFile = QtWidgets.QPushButton("Open from File...")
        buttonOpenFile.clicked.connect(self.OnOpenFile)
        buttonSaveFile = QtWidgets.QPushButton("Save to File...")
        buttonSaveFile.clicked.connect(self.OnSaveFile)
        buttonProgram = QtWidgets.QPushButton("Program to Device...")
        buttonProgram.clicked.connect(self.OnProgram)
        buttonInsert = QtWidgets.QPushButton("Insert into Page")
        buttonInsert.clicked.connect(self.OnInsert)
        buttonClose = QtWidgets.QPushButton("Close")
        buttonClose.clicked.connect(self.OnClose)

        self.comboColor = QtWidgets.QComboBox()
        for color, details in self.COLORS.items():
            self.comboColor.addItem(color)

        self.comboPage = QtWidgets.QComboBox()
        for page in self.parentWidget().GRAPHICS: self.comboPage.addItem(page)
        self.comboBlock = QtWidgets.QComboBox()
        for page in self.parentWidget().GRAPHICS_BLOCK: self.comboBlock.addItem(page)

        buttonShiftLeft = QtWidgets.QPushButton("<<")
        buttonShiftRight = QtWidgets.QPushButton(">>")
        buttonShiftLeft.clicked.connect(self.OnShiftLeft)
        buttonShiftRight.clicked.connect(self.OnShiftRight)
        shiftButtonBox = QtWidgets.QHBoxLayout()
        shiftButtonBox.addWidget(buttonShiftLeft)
        shiftButtonBox.addWidget(buttonShiftRight)
        shiftButtonBoxWidget = QtWidgets.QWidget()
        shiftButtonBoxWidget.setLayout(shiftButtonBox)

        self.toolBox = QtWidgets.QVBoxLayout()
        self.toolBox.addWidget(QtWidgets.QLabel("Paint Color:"))
        self.toolBox.addWidget(self.comboColor)
        buttonFill = QtWidgets.QPushButton("Fill")
        buttonFill.clicked.connect(self.OnFill)
        self.toolBox.addWidget(buttonFill)
        self.toolBox.addWidget(shiftButtonBoxWidget)

        self.buttonBox = QtWidgets.QHBoxLayout()
        self.buttonBox.addWidget(self.comboPage)
        self.buttonBox.addWidget(self.comboBlock)
        self.buttonBox.addWidget(buttonProgram)
        self.buttonBox.addWidget(buttonInsert)

        self.buttonBox2 = QtWidgets.QHBoxLayout()
        self.buttonBox2.addWidget(buttonOpenFile)
        self.buttonBox2.addWidget(buttonSaveFile)
        self.buttonBox2.addWidget(buttonClose)

        self.layout = QtWidgets.QGridLayout()

        self.display = QtWidgets.QGridLayout()
        self.display.setContentsMargins(0,0,0,0)
        for i in range(0, self.ledsHorizontal-1):
            for n in range(0, self.ledsVertical-1):
                pic = QClickLabel()
                pic.colorCode = self.COLORS["Off"]["code"]
                pic.setPixmap(QtGui.QPixmap(self.parentWidget().PRODUCT_ICON_PATH+"/"+self.COLORS["Off"]["pixmap"]))
                pic.setFixedWidth(self.ledWidth)
                pic.setFixedHeight(self.ledHeight)
                pic.clicked.connect(self.OnLedClicked)
                pic.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
                pic.customContextMenuRequested.connect(self.OnLedClickedSecondary)
                self.display.addWidget(pic, n, i)

        widget = QtWidgets.QWidget()
        widget.setLayout(self.display)
        widget.setFixedWidth(self.ledsHorizontal*self.ledWidth)
        widget.setFixedHeight(self.ledsVertical*self.ledHeight)
        widget.setContentsMargins(6,6,12,12)
        widget.setStyleSheet("background-color: black; border-radius: 6px;")

        widget2 = QtWidgets.QWidget()
        widget2.setLayout(self.buttonBox)

        widget3 = QtWidgets.QWidget()
        widget3.setLayout(self.buttonBox2)

        widget4 = QtWidgets.QWidget()
        widget4.setLayout(self.toolBox)

        self.layout.addWidget(widget, 0, 0)
        self.layout.addWidget(widget4, 0, 1)
        self.layout.addWidget(widget2, 1, 0)
        self.layout.addWidget(widget3, 2, 0)

        mainWidget = QtWidgets.QWidget()
        mainWidget.setLayout(self.layout)
        self.setCentralWidget(mainWidget)
        self.setWindowTitle("Graphic Editor")

    def OnLedClicked(self):
        colorInfo = self.COLORS[self.comboColor.currentText()]
        self.sender().setPixmap(QtGui.QPixmap(self.parentWidget().PRODUCT_ICON_PATH+"/"+colorInfo["pixmap"]))
        self.sender().colorCode = colorInfo["code"]

    def OnLedClickedSecondary(self):
        colorInfo = self.COLORS["Off"]
        self.sender().setPixmap(QtGui.QPixmap(self.parentWidget().PRODUCT_ICON_PATH+"/"+colorInfo["pixmap"]))
        self.sender().colorCode = colorInfo["code"]

    def OnFill(self, e):
        colorInfo = self.COLORS[self.comboColor.currentText()]
        for i in range(0, self.ledsVertical-1):
            for n in range(0, self.ledsHorizontal-1):
                widgetItem = self.display.itemAtPosition(i, n)
                widgetItem.widget().colorCode = colorInfo["code"]
                widgetItem.widget().setPixmap(QtGui.QPixmap(self.parentWidget().PRODUCT_ICON_PATH+"/"+colorInfo["pixmap"]))

    def OnShiftLeft(self, e):
        for i in range(0, self.ledsVertical-1):
            a = self.display.itemAtPosition(i, 0)
            prevColorCode = a.widget().colorCode
            for n in range(self.ledsHorizontal-2, -1, -1):
                # get widget from grid
                widgetItemNext = self.display.itemAtPosition(i, n)

                # save current color
                tmpColorCode = widgetItemNext.widget().colorCode
                #print(str(n)+" is currenty "+tmpColorCode)

                # override color from previous led
                colorInfo = self.COLORS["Off"]
                for color, details in self.COLORS.items():
                    if(details["code"] == prevColorCode): colorInfo = details
                widgetItemNext.widget().colorCode = colorInfo["code"]
                widgetItemNext.widget().setPixmap(QtGui.QPixmap(self.parentWidget().PRODUCT_ICON_PATH+"/"+colorInfo["pixmap"]))
                #print(str(n)+" overwrite with "+colorInfo["code"])

                # save color for next iteration
                prevColorCode = tmpColorCode

    def OnShiftRight(self, e):
        for i in range(0, self.ledsVertical-1):
            a = self.display.itemAtPosition(i, self.ledsHorizontal-2)
            prevColorCode = a.widget().colorCode
            for n in range(0, self.ledsHorizontal-1, 1):
                # get widget from grid
                widgetItemNext = self.display.itemAtPosition(i, n)

                # save current color
                tmpColorCode = widgetItemNext.widget().colorCode
                #print(str(n)+" is currenty "+tmpColorCode)

                # override color from previous led
                colorInfo = self.COLORS["Off"]
                for color, details in self.COLORS.items():
                    if(details["code"] == prevColorCode): colorInfo = details
                widgetItemNext.widget().colorCode = colorInfo["code"]
                widgetItemNext.widget().setPixmap(QtGui.QPixmap(self.parentWidget().PRODUCT_ICON_PATH+"/"+colorInfo["pixmap"]))
                #print(str(n)+" overwrite with "+colorInfo["code"])

                # save color for next iteration
                prevColorCode = tmpColorCode

    def OnOpenFile(self, e):
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Choose Graphic File", "", "Text Files (*.txt);;All Files (*.*)")
        if(not fileName): return

        file = open(fileName, "r")
        content = file.read()
        file.close()

        linecounter = 0
        for line in content.splitlines():
            charcounter = 0
            for char in line:
                widgetItem = self.display.itemAtPosition(linecounter, charcounter)
                if(widgetItem != None):
                    colorInfo = self.COLORS["Off"]
                    for color, details in self.COLORS.items():
                        if(details["code"] == char): colorInfo = details
                    widgetItem.widget().colorCode = colorInfo["code"]
                    widgetItem.widget().setPixmap(QtGui.QPixmap(self.parentWidget().PRODUCT_ICON_PATH+"/"+colorInfo["pixmap"]))
                charcounter += 1
            linecounter += 1

    def OnSaveFile(self, e):
        fileName, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Graphic File", "", "Text Files (*.txt);;All Files (*.*)")
        if(not fileName): return

        file = open(fileName, "w")
        file.write(self.CompileGraphicToText())
        file.close()

    def CompileGraphicToText(self):
        content = ""
        for i in range(0, self.ledsVertical-1):
            line = ""
            for n in range(0, self.ledsHorizontal-1):
                widgetItem = self.display.itemAtPosition(i, n)
                if(widgetItem != None): line += widgetItem.widget().colorCode
                else: line += "@"
            content += line + "\r\n" # windows compatible line endings
        return content

    def OnProgram(self, e):
        self.parentWidget().ld.programgraphic(self.comboPage.currentText(), self.comboBlock.currentText(), self.CompileGraphicToText())

    def OnInsert(self, e):
        self.parentWidget().textField.insertPlainText("<G"+self.comboPage.currentText()+self.comboBlock.currentText()+">")

    def OnClose(self, e):
        self.close()


class SixledsAboutWindow(QtWidgets.QDialog):
    def __init__(self, *args, **kwargs):
        super(SixledsAboutWindow, self).__init__(*args, **kwargs)
        self.InitUI()

    def InitUI(self):
        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok)
        self.buttonBox.accepted.connect(self.accept)

        self.layout = QtWidgets.QVBoxLayout(self)

        if(hasattr(self.parentWidget(), 'icon')):
            labelImage = QtWidgets.QLabel(self)
            labelImage.setPixmap(QtGui.QPixmap(self.parentWidget().PRODUCT_ICON_PATH+"/"+self.parentWidget().ABOUT_ICON))
            labelImage.setAlignment(Qt.AlignCenter)
            self.layout.addWidget(labelImage)

        labelAppName = QtWidgets.QLabel(self)
        labelAppName.setText(self.parentWidget().PRODUCT_NAME + " v" + self.parentWidget().PRODUCT_VERSION)
        labelAppName.setStyleSheet("font-weight:bold")
        labelAppName.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(labelAppName)

        labelCopyright = QtWidgets.QLabel(self)
        labelCopyright.setText(
            "<br>"
            "© 2020-2025 <a href='https://github.com/schorschii'>Georg Sieber</a> (Further Development & GUI)"
            "<br>"
            "© 2019 <a href='https://github.com/hackerdeen'>hackerdeen</a> (Base Code)"
            "<br>"
            "<br>"
            "GNU General Public License v3.0"
            "<br>"
            "<a href='"+self.parentWidget().PRODUCT_WEBSITE+"'>"+self.parentWidget().PRODUCT_WEBSITE+"</a>"
            "<br>"
        )
        labelCopyright.setOpenExternalLinks(True)
        labelCopyright.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(labelCopyright)

        labelDescription = QtWidgets.QLabel(self)
        labelDescription.setText(
            """LED Display Control Library, Command Line Utility (CLI) and Graphical User Interface (GUI)."""
            """\n"""
            """This library was made for providing Linux support for the following devices: Maplin N00GA - using the AM004-03128/03127 LED Display communication board, Velleman MML16CN, MML16R, MML24CN, McCrypt LED Light Writing 590996 (the Conrad Laufschrift)"""
        )
        labelDescription.setStyleSheet("opacity:0.8")
        labelDescription.setFixedWidth(350)
        labelDescription.setWordWrap(True)
        self.layout.addWidget(labelDescription)

        self.layout.addWidget(self.buttonBox)

        self.setLayout(self.layout)
        self.setWindowTitle("About")

class SixledsMainWindow(QtWidgets.QMainWindow):
    PRODUCT_NAME      = "sixleds GUI"
    PRODUCT_VERSION   = "0.5.0"
    PRODUCT_WEBSITE   = "https://github.com/schorschii/sixleds"
    PRODUCT_ICON      = "sixleds-icon.png"
    ABOUT_ICON        = "sixleds.png"
    SEND_ICON         = "send.png"
    PRODUCT_ICON_PATH = "/usr/share/pixmaps/sixleds"

    PAGES          = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]
    TIMES          = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]
    SCHEDULES      = {"A":{}, "B":{}, "C":{}, "D":{}, "E":{}}
    BRIGHTNESS     = ["A", "B", "C", "D"]
    GRAPHICS       = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P"]
    GRAPHICS_BLOCK = ["1", "2", "3", "4", "5", "6", "7", "8"]

    serialPorts    = []
    serialPort     = "/dev/ttyUSB0"
    configFile     = "~/.config/sixleds/config"
    deviceId       = 0

    page          = "A"
    line          = "1"
    leadingFx     = "E"
    speed         =  2
    displayFx     = "A"
    displayMethod = "Q" # calculated from speed and displayFx
    waitTime      = "A"
    laggingFx     = "E"

    def __init__(self, *args, **kwargs):
        super(SixledsMainWindow, self).__init__(*args, **kwargs)
        self.serialPorts = self.GetSerialPorts()
        if(len(self.serialPorts) > 0): self.serialPort = self.serialPorts[0]
        self.SetupConnection(message=False)
        self.InitUI()

    def GetSerialPorts(self):
        if platform.system() == 'Windows':
            ports = ['COM%s' % (i + 1) for i in range(10)]
        elif platform.system() == 'Linux':
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif platform.system() == 'Darwin':
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')
        result = []
        for port in ports:
            if("bluetooth" in port): continue # macOS
            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except(OSError, serial.SerialException):
                pass
        return result

    def InitUI(self):
        # Menubar
        mainMenu = self.menuBar()

        # File Menu
        fileMenu = mainMenu.addMenu('&File')

        selectPortAction = QtGui.QAction('Select Serial &Port...', self)
        selectPortAction.setShortcut('Ctrl+P')
        selectPortAction.triggered.connect(self.OnSelectSerialPort)
        fileMenu.addAction(selectPortAction)
        selectDeviceIdAction = QtGui.QAction('Select &Device ID...', self)
        selectDeviceIdAction.setShortcut('Ctrl+I')
        selectDeviceIdAction.triggered.connect(self.OnChangeDeviceId)
        fileMenu.addAction(selectDeviceIdAction)
        fileMenu.addSeparator()
        sendAction = QtGui.QAction('&Send And Save Page', self)
        sendAction.setShortcut('Ctrl+S')
        sendAction.triggered.connect(self.OnSendPage)
        fileMenu.addAction(sendAction)
        fileMenu.addSeparator()
        sendAction = QtGui.QAction('Create/Edit &Graphic...', self)
        sendAction.setShortcut('Ctrl+G')
        sendAction.triggered.connect(self.OnOpenGraphicDialog)
        fileMenu.addAction(sendAction)
        fileMenu.addSeparator()
        quitAction = QtGui.QAction('&Quit', self)
        quitAction.setShortcut('Ctrl+Q')
        quitAction.triggered.connect(self.OnQuit)
        fileMenu.addAction(quitAction)

        # Edit Menu
        editMenu = mainMenu.addMenu('&Edit')

        cutAction = QtGui.QAction('&Cut', self)
        cutAction.setShortcut('Ctrl+X')
        cutAction.triggered.connect(self.OnCut)
        editMenu.addAction(cutAction)

        copyAction = QtGui.QAction('C&opy', self)
        copyAction.setShortcut('Ctrl+C')
        copyAction.triggered.connect(self.OnCopy)
        editMenu.addAction(copyAction)

        pasteAction = QtGui.QAction('&Paste', self)
        pasteAction.setShortcut('Ctrl+V')
        pasteAction.triggered.connect(self.OnPaste)
        editMenu.addAction(pasteAction)

        pasteAction = QtGui.QAction('&Delete', self)
        pasteAction.setShortcut('Ctrl+D')
        pasteAction.triggered.connect(self.OnDelete)
        editMenu.addAction(pasteAction)

        # Page Menu
        pageMenu = mainMenu.addMenu('&Page')

        self.leadingFxMenu = pageMenu.addMenu('&Leading Effect')
        leadingFxActionGroup = QtGui.QActionGroup(self)
        leadingFxActionGroup.setExclusive(True)
        leadingFx = {
            'A': 'Immediate',
            'B': 'Xopen',
            'C': 'Curtain Up',
            'D': 'Curtain Down',
            'E': 'Scroll Left',
            'F': 'Scroll Right',
            'G': 'Vopen',
            'H': 'Vclose',
            'I': 'Scroll Up',
            'J': 'Scroll Down',
            'K': 'Hold',
            'L': 'Snow',
            'M': 'Twinkle',
            'N': 'Block Move',
            'P': 'Random'
        }
        for key, value in leadingFx.items():
            actionButton = leadingFxActionGroup.addAction(QtGui.QAction(value, self, checkable=True))
            actionButton.triggered.connect(partial(self.OnSetLeadingFx, key, actionButton))
            actionButton.fxCode = key
            self.leadingFxMenu.addAction(actionButton)

        self.speedMenu = pageMenu.addMenu('&Move Speed')
        speedActionGroup = QtGui.QActionGroup(self)
        speedActionGroup.setExclusive(True)
        speed = {
            4: '1 Slow',
            3: '2',
            2: '3',
            1: '4 Fast'
        }
        for key, value in speed.items():
            actionButton = speedActionGroup.addAction(QtGui.QAction(value, self, checkable=True))
            actionButton.triggered.connect(partial(self.OnSetSpeed, key, actionButton))
            actionButton.fxCode = key
            self.speedMenu.addAction(actionButton)

        self.displayFxMenu = pageMenu.addMenu('&Display Effect')
        displayFxActionGroup = QtGui.QActionGroup(self)
        displayFxActionGroup.setExclusive(True)
        displayFx = {
            'A': 'Normal',
            'B': 'Blinking',
            'C': 'Song 1',
            'D': 'Song 2',
            'E': 'Song 3'
        }
        for key, value in displayFx.items():
            actionButton = displayFxActionGroup.addAction(QtGui.QAction(value, self, checkable=True))
            actionButton.triggered.connect(partial(self.OnSetDisplayFx, key, actionButton))
            actionButton.fxCode = key
            self.displayFxMenu.addAction(actionButton)

        actionButton = QtGui.QAction('Display &Time...', self)
        actionButton.triggered.connect(self.OnSetDisplayTime)
        pageMenu.addAction(actionButton)

        self.closingFxMenu = pageMenu.addMenu('&Closing Effect')
        closingFxActionGroup = QtGui.QActionGroup(self)
        closingFxActionGroup.setExclusive(True)
        closingFx = {
            'A': 'Immediate',
            'B': 'Xopen',
            'C': 'Curtain Up',
            'D': 'Curtain Down',
            'E': 'Scroll Left',
            'F': 'Scroll Right',
            'G': 'Vopen',
            'H': 'Vclose',
            'I': 'Scroll Up',
            'J': 'Scroll Down',
            'K': 'Hold'
        }
        for key, value in closingFx.items():
            actionButton = closingFxActionGroup.addAction(QtGui.QAction(value, self, checkable=True))
            actionButton.triggered.connect(partial(self.OnSetClosingFx, key, actionButton))
            actionButton.fxCode = key
            self.closingFxMenu.addAction(actionButton)

        # Insert Menu
        insertMenu = mainMenu.addMenu('&Insert')

        fontMenu = insertMenu.addMenu('&Font')
        font = {
            '<AA>': '4x7 (narrow size)',
            '<AC>': '5x7 (normal size)',
            '<AB>': '6x7 (bold size)',
            '<AD>': '7x13 (large size)',
            '<AE>': '5x8 (long size)'
        }
        for key, value in font.items():
            actionButton = QtGui.QAction(value, self)
            actionButton.triggered.connect(partial(self.OnInsertCmd, key, actionButton))
            fontMenu.addAction(actionButton)

        colorMenu = insertMenu.addMenu('C&olor')
        color = {
            '<CB>': 'Red',
            '<CE>': 'Green',
            '<CH>': 'Orange',
            '<CL>': 'Inversed Red',
            '<CM>': 'Inversed Green',
            '<CN>': 'Inversed Orange',
            '<CP>': 'Red On Green',
            '<CQ>': 'Green On Red',
            '<CR>': 'RYG',
            '<CS>': 'Rainbow'
        }
        for key, value in color.items():
            actionButton = QtGui.QAction(value, self)
            actionButton.triggered.connect(partial(self.OnInsertCmd, key, actionButton))
            colorMenu.addAction(actionButton)

        insertMenu.addSeparator()
        specialFxMenu = insertMenu.addMenu('Special &Function')
        specialFx = {
            '<BA>': 'Bell',
            '<KD>': 'Date',
            '<KT>': 'Time'
        }
        for key, value in specialFx.items():
            actionButton = QtGui.QAction(value, self)
            actionButton.triggered.connect(partial(self.OnInsertCmd, key, actionButton))
            specialFxMenu.addAction(actionButton)

        actionButton = QtGui.QAction('&Special Char...', self)
        actionButton.triggered.connect(self.OnInsertSpecialChar)
        insertMenu.addAction(actionButton)

        actionButton = QtGui.QAction('&Graphic...', self)
        actionButton.triggered.connect(self.OnInsertGraphic)
        insertMenu.addAction(actionButton)

        # Commands Menu
        commandsMenu = mainMenu.addMenu('&Commands')
        actionButton = QtGui.QAction('Send &Raw Command...', self)
        actionButton.setShortcut('F3')
        actionButton.triggered.connect(self.OnSendMessage)
        commandsMenu.addAction(actionButton)
        actionButton = QtGui.QAction('Set &Default Run Page...', self)
        actionButton.setShortcut('F4')
        actionButton.triggered.connect(self.OnSetDefaultRunPage)
        commandsMenu.addAction(actionButton)

        commandsMenu.addSeparator()
        actionButton = QtGui.QAction('Set &ID...', self)
        actionButton.setShortcut('F5')
        actionButton.triggered.connect(self.OnSetId)
        commandsMenu.addAction(actionButton)
        actionButton = QtGui.QAction('Set &Clock', self)
        actionButton.setShortcut('F6')
        actionButton.triggered.connect(self.OnSetClock)
        commandsMenu.addAction(actionButton)
        actionButton = QtGui.QAction('Set &Brightness...', self)
        actionButton.setShortcut('F7')
        actionButton.triggered.connect(self.OnSetBrightness)
        commandsMenu.addAction(actionButton)
        actionButton = QtGui.QAction('Set &Schedule...', self)
        actionButton.setShortcut('F8')
        actionButton.triggered.connect(self.OnSetSchedule)
        commandsMenu.addAction(actionButton)

        commandsMenu.addSeparator()
        actionButton = QtGui.QAction('Delete All Content (&Factory Reset)', self)
        actionButton.setShortcut('F9')
        actionButton.triggered.connect(self.OnFactoryReset)
        commandsMenu.addAction(actionButton)

        # Help Menu
        helpMenu = mainMenu.addMenu('&Help')

        actionButton = QtGui.QAction('&Website/Updates', self)
        actionButton.setShortcut('F1')
        actionButton.triggered.connect(self.OnOpenReadme)
        helpMenu.addAction(actionButton)

        actionButton = QtGui.QAction('&About', self)
        actionButton.setShortcut('F2')
        actionButton.triggered.connect(self.OnOpenAboutDialog)
        helpMenu.addAction(actionButton)

        # Statusbar
        self.statusBar = self.statusBar()

        # Window Content
        hbox = QtWidgets.QHBoxLayout()

        self.textField = QtWidgets.QTextEdit()
        font = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.SystemFont.FixedFont)
        font.setPointSize(14)
        self.textField.setFont(font)
        self.textField.textChanged.connect(self.OnTextChanged)
        self.listBox = QtWidgets.QListWidget()
        self.listBox.currentTextChanged.connect(self.OnPageChanged)
        for page in self.PAGES: self.listBox.addItem(page)
        self.listBox.setCurrentRow(0)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        splitter.addWidget(self.listBox)
        splitter.addWidget(self.textField)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 8)

        hbox.addWidget(splitter)

        widget = QtWidgets.QWidget(self)
        widget.setLayout(hbox)
        self.setCentralWidget(widget)

        # Icon Selection
        if(getattr(sys, 'frozen', False)):
            # included via pyinstaller (Windows & macOS)
            self.PRODUCT_ICON_PATH = sys._MEIPASS
        elif(path.isfile(getcwd()+'/assets/icons/'+self.PRODUCT_ICON)):
            # ad hoc execution (not installed via deb package)
            self.PRODUCT_ICON_PATH = getcwd()+'/assets/icons/'
        self.iconPath = path.join(self.PRODUCT_ICON_PATH, self.PRODUCT_ICON)
        if(path.exists(self.iconPath)):
            self.icon = QtGui.QIcon(self.iconPath)
            self.setWindowIcon(self.icon)

        # Toolbar
        toolbar = QtWidgets.QToolBar(self)
        self.addToolBar(toolbar)
        self.portAction = QtGui.QAction('', self)
        self.portAction.triggered.connect(self.OnSelectSerialPort)
        toolbar.addAction(self.portAction)
        self.deviceAction = QtGui.QAction('', self)
        self.deviceAction.triggered.connect(self.OnChangeDeviceId)
        toolbar.addAction(self.deviceAction)
        toolbar.addSeparator()
        self.sendAction = QtGui.QAction('Send And Save Page', self)
        self.sendAction.triggered.connect(self.OnSendPage)
        toolbar.addAction(self.sendAction)

        # Window Settings
        self.setMinimumSize(520, 410)
        self.setWindowTitle(self.PRODUCT_NAME+" v"+self.PRODUCT_VERSION)

        # Load Initial Page
        self.OnTextChanged()
        self.UpdatePortAndDeviceText()

        # Show Donation Note
        self.statusBar.showMessage("If you like sixleds please consider making a donation to support further development ("+self.PRODUCT_WEBSITE+").")

    def UpdatePortAndDeviceText(self):
        self.portAction.setText('Port: '+self.serialPort)
        self.deviceAction.setText('Device: '+str(self.deviceId))

    def OnTextChanged(self):
        self.statusBar.showMessage("Page: "+self.page+", Chars: "+str(len(self.textField.toPlainText())))

    def OnOpenReadme(self, e):
        webbrowser.open(self.PRODUCT_WEBSITE)

    def OnOpenGraphicDialog(self, e):
        dlg = SixledsGraphicWindow(self)
        dlg.show()

    def OnOpenAboutDialog(self, e):
        dlg = SixledsAboutWindow(self)
        dlg.exec()

    def OnInsertSpecialChar(self, e):
        displayItems = []
        for key, value in sixleds.opage.ttable.items():
            displayItems.append(chr(key))
        item, ok = QtWidgets.QInputDialog.getItem(self, "Insert Special Char", None, displayItems, 0, False)
        if ok and item:
            self.textField.insertPlainText(item)

    def OnInsertGraphic(self, e):
        graphic, ok = QtWidgets.QInputDialog.getItem(self, "Insert Graphic", "Please choose the graphic to insert\n(Please program your custom graphic to device first via 'Create/Edit Graphic' tool)", self.GRAPHICS, 0, False)
        if(not(ok and graphic)): return

        block, ok = QtWidgets.QInputDialog.getItem(self, "Insert Graphic", "Please choose the graphic block", self.GRAPHICS_BLOCK, 0, False)
        if(not(ok and block)): return

        self.textField.insertPlainText("<G"+graphic+block+">")

    def OnPageChanged(self, e):
        if(len(self.listBox.selectedItems()) == 0): return
        self.page = self.PAGES[self.listBox.currentRow()]
        value = self.ld.getline(self.page)
        self.textField.setPlainText("")
        if(value != None):
            self.textField.setPlainText(value.MM)

            self.leadingFx = value.FX
            for item in self.leadingFxMenu.actions():
                if(value.FX == item.fxCode):
                    item.setChecked(True)

            self.displayMethod = value.MX
            if(value.MX == 'A'):
                self.speed = 4
                self.displayFx = 'A'
            elif(value.MX == 'B'):
                self.speed = 4
                self.displayFx = 'B'
            elif(value.MX == 'C'):
                self.speed = 4
                self.displayFx = 'C'
            elif(value.MX == 'D'):
                self.speed = 4
                self.displayFx = 'D'
            elif(value.MX == 'E'):
                self.speed = 4
                self.displayFx = 'E'
            elif(value.MX == 'Q'):
                self.speed = 3
                self.displayFx = 'A'
            elif(value.MX == 'R'):
                self.speed = 3
                self.displayFx = 'B'
            elif(value.MX == 'S'):
                self.speed = 3
                self.displayFx = 'C'
            elif(value.MX == 'T'):
                self.speed = 3
                self.displayFx = 'D'
            elif(value.MX == 'U'):
                self.speed = 3
                self.displayFx = 'E'
            elif(value.MX == 'a'):
                self.speed = 2
                self.displayFx = 'A'
            elif(value.MX == 'b'):
                self.speed = 2
                self.displayFx = 'B'
            elif(value.MX == 'c'):
                self.speed = 2
                self.displayFx = 'C'
            elif(value.MX == 'd'):
                self.speed = 2
                self.displayFx = 'D'
            elif(value.MX == 'e'):
                self.speed = 2
                self.displayFx = 'E'
            elif(value.MX == 'q'):
                self.speed = 1
                self.displayFx = 'A'
            elif(value.MX == 'r'):
                self.speed = 1
                self.displayFx = 'B'
            elif(value.MX == 's'):
                self.speed = 1
                self.displayFx = 'C'
            elif(value.MX == 't'):
                self.speed = 1
                self.displayFx = 'D'
            elif(value.MX == 'u'):
                self.speed = 1
                self.displayFx = 'E'

            for item in self.speedMenu.actions():
                if(self.speed == item.fxCode):
                    item.setChecked(True)
            for item in self.displayFxMenu.actions():
                if(self.displayFx == item.fxCode):
                    item.setChecked(True)

            self.laggingFx = value.FY
            for item in self.closingFxMenu.actions():
                if(value.FY == item.fxCode):
                    item.setChecked(True)

    def OnCut(self, e):
        self.textField.cut()

    def OnCopy(self, e):
        self.textField.copy()

    def OnPaste(self, e):
        self.textField.paste()

    def OnDelete(self, e):
        self.textField.insertPlainText("")

    def OnSendMessage(self, e):
        if(self.SetupConnection()):
            item, ok = QtWidgets.QInputDialog.getText(self, "Send Command", "Enter a raw command to send")
            if ok and item:
                self.ld.send(item)

    def OnSetDefaultRunPage(self, e):
        if(self.SetupConnection()):
            item, ok = QtWidgets.QInputDialog.getItem(self, "Default Run Page", "Please select a default run page", self.PAGES, 0, False)
            if ok and item:
                self.ld.send('<RP'+item+'>')

    def OnChangeDeviceId(self, e):
        if(self.SetupConnection()):
            item, ok = QtWidgets.QInputDialog.getInt(self, "Change Device ID", "Enter the ID of the device which should be controlled (0..255).\nZero is the broadcast which addresses all connected devices on the serial port.", self.deviceId, 0, 255)
            if ok:
                self.deviceId = item
                self.SetupConnection()
                self.UpdatePortAndDeviceText()

    def OnSetId(self, e):
        if(self.SetupConnection()):
            item, ok = QtWidgets.QInputDialog.getInt(self, "Set Device ID", "Enter the ID which should be assigned to the device (1..255)", self.deviceId, 1, 255)
            if ok:
                self.ld.setid(newid=int(item))
                self.deviceId = item
                self.UpdatePortAndDeviceText()

    def OnSetClock(self, e):
        if(self.SetupConnection()):
            self.ld.setclock()

    def OnSetBrightness(self, e):
        if(self.SetupConnection()):
            item, ok = QtWidgets.QInputDialog.getItem(self, "Set Brightness Level", "Please choose new brightness level", self.BRIGHTNESS, 0, False)
            if ok and item:
                self.ld.brightness(item)

    def OnSetSchedule(self, e):
        if(self.SetupConnection()):
            dlg = SixledsScheduleWindow(self)
            dlg.show()

    def OnFactoryReset(self, e):
        if(self.SetupConnection()):
            self.ld.send('<D*>')

    def OnInsertCmd(self, cmd, e):
        self.textField.insertPlainText(cmd)

    def OnSetDisplayTime(self, e):
        if(self.SetupConnection()):
            item, ok = QtWidgets.QInputDialog.getItem(self, "Display Time", "Please select the display (wait) time.", self.TIMES, self.TIMES.index(self.waitTime), False)
            if ok and item:
                self.waitTime = item

    def OnSetLeadingFx(self, fx, menuItem, e):
        self.leadingFx = fx

    def OnSetSpeed(self, speed, menuItem, e):
        self.speed = speed
        self.CalcDisplayMethod()

    def OnSetDisplayFx(self, fx, menuItem, e):
        self.displayFx = fx
        self.CalcDisplayMethod()

    def CalcDisplayMethod(self):
        DISPLAY_METHOD_MATRIX = {
            1 : { "A":"A", "B":"B", "C":"C", "D":"D", "E":"E" },
            2 : { "A":"Q", "B":"R", "C":"S", "D":"T", "E":"U" },
            3 : { "A":"a", "B":"b", "C":"c", "D":"d", "E":"e" },
            4 : { "A":"q", "B":"r", "C":"s", "D":"t", "E":"u" },
        }
        self.displayMethod = "Q" # fallback to default
        if(self.speed in DISPLAY_METHOD_MATRIX and self.displayFx in DISPLAY_METHOD_MATRIX[self.speed]):
            self.displayMethod = DISPLAY_METHOD_MATRIX[self.speed][self.displayFx]

    def OnSetClosingFx(self, fx, menuItem, e):
        self.laggingFx = fx

    def SetupConnection(self, message=True):
        logging.getLogger().setLevel(logging.INFO)
        if(hasattr(self, 'ld') and self.ld.isopen()): self.ld.close()
        self.ld = sixleds.sixleds(dev=self.serialPort, conf=self.configFile, device=self.deviceId)
        if(self.ld.ser == None):
            if(message):
                messageText = "Cannot send data. Please check if serial port »"+self.serialPort+"« is correct and if you have privileges to use this port (add your user to group dialout via »usermod -a -G dialout USERNAME« and log in again).\n\nIf the error persists, please use the command line tool to examine the error."
                if(platform.system() == 'Windows' or platform.system() == 'Darwin'):
                    messageText = "Cannot send data. Please check if serial port »"+self.serialPort+"« is correct.\n\nIf the error persists, please use the command line tool to examine the error."
                QtWidgets.QMessageBox.critical(self, "Connection Error", messageText)
            return False
        else:
            return True

    def OnSelectSerialPort(self, e):
        item, ok = QtWidgets.QInputDialog.getItem(self, "Port Selection", "Please select serial port which should be used to communicate with the device.", self.serialPorts, 0, False)
        if ok and item:
            self.serialPort = item
            self.SetupConnection()
            self.UpdatePortAndDeviceText()

    def OnSendPage(self, e):
        if(self.SetupConnection()):
            self.ld.updateline(self.page, self.textField.toPlainText(), self.line, self.leadingFx, self.displayMethod, self.waitTime, self.laggingFx)
            self.ld.pushchanges()

    def OnQuit(self, e):
        self.close()


def main():
    app = QtWidgets.QApplication(sys.argv)
    SixledsMainWindow().show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
