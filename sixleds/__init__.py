#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys, serial, logging
from time import sleep, localtime, strftime
from datetime import datetime
import _pickle as pickle
import platform
import traceback


class dt(datetime):
    ''' Datetime Subclass
    A datetime object with a special output for the display schedule
    '''

    def sched(self):
        """Output the date in the format for the display.

        Returns
        ------
        string
            Datetime in format 'yymmddHHMM'
            yy=Year, mm=Month, dd=Day, HH=Hour, MM=Minute
        """
        return self.strftime("%y%m%d%H%M")


class oschedule():
    """An object to hold and modify a schedule definition

    It holds a start date aend date a list of pages to show
    in order and active flag to indicate whether it is active
    on the display
    """

    active = True
    changed = True
    PP = ''

    def __init__(self, PP='', start='00', end='99'):
        """ Create a scedule

        A schedule has a start date an end date and string of pages to dislay,
        It can ba active or not.

        Parameters
        ------
        PP: string, default='A'
            The pages to display in the scedule
        start:
            passed to date function
        end:
            passd to the date function

        Return
        ------
        :obj: `oschedule`
        """
        self.st = self.date(start)
        self.en = self.date(end)
        self.PP = PP

    def date(self, date=''):
        """Returns a dt object of the date enterd in display format

        Parameters
        ------
        date : dt
            Will use a dt object if passed
        date : datetime
            will accept a datetime object and output dt object
        date : string
            Datetime in format 'yymmddHHMM'
            yy=Year, mm=Month, dd=Day, HH=Hour, MM=Minute
            missing = 00, our of range rounded to nearest

        Return
        ------
        dt
            datetime subclass of the entered datetime.
        """
        if type(date) == dt:
            return date
        if type(date) == datetime:
            return dt(*(datetime.timetuple()[:7]))
        elif date != '':
            yy = int(date[0:2] if date[0:2] != '' else '0') + 2000
            mm = int(date[2:4] if date[2:4] != '' else '1')
            if mm > 12:
                mm = 12
            if mm < 1:
                mm = 1
            dd = int(date[4:6] if date[4:6] != '' else '1')
            if dd > 31:
                dd = 31
            if dd < 1:
                dd = 1
            HH = int(date[6:8] if date[6:8] != '' else '0')
            if HH > 23:
                HH = 23
            MM = int(date[8:10] if date[8:10] != '' else '0')
            if MM > 59:
                MM = 59
            return dt(yy,mm,dd,HH,MM)

    def start(self, st):
        """Set the start datetime when the schedule will be active

        Parameters
        ------
        st: :obj:`dt`, :obj:`datetime`,string
             Passes to date function to return a dt object
        """
        self.st = self.date(st)
        self.modified()

    def end(self, en):
        """Set the start datetime when the schedule will be active

        Parameters
        ------
        st: :obj:`dt`, :obj:`datetime`,string
             Passes to date function to return a dt object
        """
        self.en = self.date(en)
        self.modified()

    def pages(self, PP=''):
        """will substitute the pages shown in the schedule for the ones in the list

        Paramaters
        ------
        PP: string
            A string of Pages. eg "ABC"

        Return
        ------
        string
            the pages set to display in the schedule
        """
        if PP != '':
            self.PP = PP
            self.modified()

        return self.PP

    def activate(self, active=True):
        """ This will activate this Schedule

        Active schedules are sent to the display deleted devices are deleted from the device.

        Parameters
        ------
        active: bool, default=True
            Sets whether the device is active or not.
        """
        if self.active != active:
            self.active = active
            self.modified()

    def modified(self, changed=True):
        """Check if modified, or set to modified (changed)

        Send the function a True to set the schedule to modified or just call the
        function with no parameters to reset it will return whether it was modied or not.

        Parameters
        ------
        changed: bool, default=True
            Will set the self.changed value to this

        Return
        ------
        bool:
            the value of changed on call on fucntion.
        """
        r = self.changed
        self.changed = changed
        return r

    def packet(self):
        """Returns the formatted packet to send to the screen.

        the packed does not contain the schedule identifier or checksum

        Return
        ------
        string:
            formatted packet string
        """
        return self.st.sched() + self.en.sched() + self.PP


class opage():
    """A page for a line which can be displayed

    """
    MM = ''
    FX = ''
    MX = ''
    WX = ''
    FY = ''
    changed = True
    ttable ={
        ord('€'): '<U00>', ord('↑'): '<U01>', ord('↓'): '<U02>', ord('˥'): '<U03>',
        ord('˦'): '<U04>', ord('˨'): '<U05>', ord('˩'): '<U06>', ord('└'): '<U07>',
        ord('┴'): '<U08>', ord('├'): '<U09>', ord('┬'): '<U0A>', ord('─'): '<U0B>',
        ord('┼'): '<U0C>', ord('┘'): '<U0D>', ord('┌'): '<U0E>', ord('█'): '<U0F>',

        ord('▄'): '<U10>', ord('▌'): '<U11>', ord('▐'): '<U12>', ord('▀'): '<U13>',
        ord('α'): '<U14>', ord('β'): '<U15>', ord('Γ'): '<U16>', ord('ä'): '<U17>',
        ord('Σ'): '<U18>', ord('σ'): '<U19>', ord('μ'): '<U1A>', ord('τ'): '<U1B>',
        ord('Φ'): '<U1C>', ord('≈'): '<U1D>', ord('Ω'): '<U1E>', ord('δ'): '<U1F>',

        ord('∞'): '<U20>', ord('λ'): '<U21>', ord('¢'): '<U22>', ord('£'): '<U23>',
        ord('♉'): '<U24>', ord('¥'): '<U25>', ord('→'): '<U26>', ord('←'): '<U27>',
        ord('¿'): '<U28>', ord('©'): '<U29>', ord('ª'): '<U2A>', ord('≥'): '<U2B>',
        ord('Ɛ'): '<U2C>', ord('∩'): '<U2D>', ord('®'): '<U2E>', ord('�'): '<U2F>',

        ord('š'): '<U30>', ord('±'): '<U31>', ord('²'): '<U32>', ord('³'): '<U33>',
        ord('ž'): '<U34>', ord('Ÿ'): '<U35>', ord('¶'): '<U36>', ord('ɶ'): '<U37>',
        ord('Š'): '<U38>', ord('¹'): '<U39>', ord('⁰'): '<U3A>', ord('≤'): '<U3B>',
        ord('¼'): '<U3C>', ord('½'): '<U3D>', ord('¤'): '<U3E>', ord('¿'): '<U3F>',

        ord('À'): '<U40>', ord('Á'): '<U41>', ord('Â'): '<U42>', ord('Ã'): '<U43>',
        ord('Ä'): '<U44>', ord('Å'): '<U45>', ord('Æ'): '<U46>', ord('Ç'): '<U47>',
        ord('È'): '<U48>', ord('É'): '<U49>', ord('Ê'): '<U4A>', ord('Ë'): '<U4B>',
        ord('Ì'): '<U4C>', ord('Í'): '<U4D>', ord('Î'): '<U4E>', ord('Ï'): '<U4F>',

        ord('Ð'): '<U50>', ord('Ñ'): '<U51>', ord('Ò'): '<U52>', ord('Ó'): '<U53>',
        ord('Ô'): '<U54>', ord('Õ'): '<U55>', ord('Ö'): '<U56>', ord('Ž'): '<U57>',
        ord('Ø'): '<U58>', ord('Ù'): '<U59>', ord('Ú'): '<U5A>', ord('Û'): '<U5B>',
        ord('Ü'): '<U5C>', ord('Ý'): '<U5D>', ord('Þ'): '<U5E>', ord('ß'): '<U5F>',

        ord('à'): '<U60>', ord('á'): '<U61>', ord('â'): '<U62>', ord('ã'): '<U63>',
        ord('ä'): '<U64>', ord('å'): '<U65>', ord('æ'): '<U66>', ord('ç'): '<U67>',
        ord('è'): '<U68>', ord('é'): '<U69>', ord('ê'): '<U6A>', ord('ë'): '<U6B>',
        ord('ì'): '<U6C>', ord('í'): '<U6D>', ord('î'): '<U6E>', ord('ï'): '<U6F>',

        ord('ð'): '<U70>', ord('ñ'): '<U71>', ord('ò'): '<U72>', ord('ó'): '<U73>',
        ord('ô'): '<U74>', ord('õ'): '<U75>', ord('ö'): '<U76>', ord('…'): '<U77>',
        ord('ø'): '<U78>', ord('ù'): '<U79>', ord('ú'): '<U7A>', ord('û'): '<U7B>',
        ord('ü'): '<U7C>', ord('ý'): '<U7D>', ord('þ'): '<U7E>', ord('ÿ'): '<U7F>',
    }

    def __init__(self, MM, FX='E', MX='Q', WX='A', FY='E'):
        """Create a page for a line

        This will hold a configuration,

        Parameters
        ------
        MM: string
            The Message string,
        FX: string, defailt='E'
            The Leadin animation (see leadin)
        MX: string, defailt='Q'
            The Display mode for the page (see display)
        WX: string, defailt='A'
            The wait time (see wait)
        FY: string, defailt='E'
            The Lagging animation (see lagging)

        Return
        ------
        :obj: `opage`
        """
        self.leadin(FX)
        self.display(MX)
        self.wait(WX)
        self.lagging(FY)
        self.message(MM)
        self.modified()


    def leadin(self, FX=''):
        """Set the leadin animation for the page

        Parameters
        ------
        FX: character
            One of'ABCDEFGHIJKLMNOPQRS'

        Return
        ------
        character
            The value of self.FX
        """
        if len(FX) == 1 and FX in 'ABCDEFGHIJKLMNOPQRS' and FX != self.FX:
            self.FX = FX
            self.modified()
        return self.FX

    def display(self, MX=''):
        """Sets the Display Mode for the Page

        Parameters
        ------
        MX: character
            One of 'ABRSabqr'

        Return
        ------
        character
            the value of FX
        """
        if len(MX) == 1 and MX in 'ABCDEQRSTUabcdeqrstu' and MX != self.MX:
            self.MX = MX
            self.modified()
        return self.MX

    def wait(self, WX=''):
        """Set the Wait time between leadin and lagging animations for the page

        Parameters
        ------
        WX: character
            One of 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            Letter denotes 0.5, 1, 2, 3 .. 25 Seconds

        Return
        ------
        character
            The value of self.WX
        """
        if len(WX) == 1 and WX in 'ABCDEFGHIJKLMNOPQRSUVWXYZ' and WX != self.WX:
            self.WX = WX
            self.modified()
        return self.WX

    def lagging(self, FY=''):
        """Set the lagging animation for the page

        Parameters
        ------
        FY: character
            One of'ABCDEFGHIJK'

        Return
        ------
        character
            The value of self.FY
        """
        if len(FY) == 1 and FY in 'ABCDEFGHIJK' and FY != self.FY:
            self.FY = FY
            self.modified()
        return self.FY

    def message(self, MM=''):
        """The Message to Display

        The string can have markup modifiers (magic strings), see help text

        Parameters
        ------
        MM: string, default=''
            the string to display when the page i activaten by a schedule

        Return
        ------
        string:
            the message - self.MM
        """
        if len(MM) > 0:
            self.MM = MM
            self.modified()
        return self.MM

    def modified(self, changed=True):
        """Check if modified, or set to modified (changed)

        Send the function a True to set the page to modified, or just call the
        function with no parameters to reset and return whether it was modied or not.

        Parameters
        ------
        changed: bool, default=False
            Will set the modified

        Return
        ------
        bool:
            the value of changed on call on fucntion.
        """
        r = self.changed
        self.changed = changed
        return r

    def packet(self):
        """Returns the formatted packet to send to the screen.

        The packet does not contain the line, page identifier or checksum

        Return
        ------
        string:
            formatted packet string
        """
        return '<F' + self.FX + '><M' + self.MX + '><W' + self.WX + '><F' + self.FY + '>' + self.MM.translate(self.ttable)


class sixleds():
    """A Class to store the lcd setting for the display in the space."""

    lines = {'1':{}}
    schedules = {}
    defaultPage = 'A'


    def __init__(self, dev='/dev/ttyUSB0', conf='/var/lib/sixleds/config', device=0x01):
        ''' Create the connection to the display

        Set up serial connections.
        reload the config saved

        Paramaters
        ------
        dev: string, default='/dev/ttyUSB0'
            The serial device the display is connected to.
        conf: string, default='/var/lib/sixleds/status'
            The saved configuration for the display will add '-<device>.conf'
            to whatever you enter here.
            NOTE! unsire the directory exists and is +wr by service user and group.
        device: byte, default=0x01
            The device identifier

        Return
        ------
        :obj: 'sixleds'
            The sixleds Object
        '''
        self.device=device
        try:
            self.ser = serial.Serial(
                port=dev,
                baudrate=9600,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )
        except serial.SerialException as e:
            traceback.print_exc()
            self.error = "Failed to connect to Display on {0}: Serial Error{1}: {2}".format(dev, e.errno, e.strerror)
            logging.warning(self.error)
            self.ser = None

        if self.connected():
            self.config = os.path.expanduser(conf + '-%02x.conf' % self.device)
            self.confget()

    def connected(self):
        '''Is the display connected
        Return
        ------
        :bool:
            True Connected to display | False Not connected '''
        return True if isinstance(self.ser, serial.Serial) else False

    def confput(self):
        '''Save the current config to disk'''
        if not os.path.isdir(os.path.dirname(self.config)):
            os.makedirs(os.path.dirname(self.config), exist_ok=True)
        if os.path.isfile(self.config):
            # Clear file
            os.remove(self.config)
        try:
            with open(self.config, "wb") as f:
                pickle.dump((self.lines,self.schedules,self.defaultPage), f)
        except IOError as e:
            logging.warning("Failed to save config: I/O error({0}): {1}".format(e.errno, e.strerror))

    def confget(self):
        '''Retrieve the config from the disk'''
        logging.info( "Using Config File: " + self.config )
        if os.path.isfile(self.config):
            try:
                with open(self.config, "rb") as f:
                    self.lines,self.schedules,self.defaultPage = pickle.load(f)
            except:
                pass

    def isopen(self):
        '''Check if serial interface is open

        Return
        ------
        bool:
            whether the serial interface is open
        '''
        if(self.ser is None):
            return False
        return self.ser.isOpen()

    def close(self):
        '''Close the serial interface'''
        return self.ser.close()

    def chsum(self, packet):
        '''Returns a checksum for the packet contents

        Paramaters
        ------
        packet: string
            the packed to generate the checksum for.

        Return
        ------
        string
            A hex value of the checksum for the packet
        '''
        cs = 0
        for c in packet:
            cs ^= ord(c)
        return format(cs, 'x').zfill(2).upper()

    def updateline(self, page, message, line='1', FX='E', MX='Q', WX='A', FY='E'):
        '''Update the page and message on a line or create one

        If the page does not exist it will create one with default settings

        Paramaters
        -------
        page: string
            The page identifier
        message: string
            A message to display when page activated, for markup see the opage.message function.
        line: char, default='1'
            the line the page will be assigned to.
        '''
        if page in self.lines[line]:
            o = self.lines[line][page]
            o.message(message)
            o.leadin(FX)
            o.display(MX)
            o.wait(WX)
            o.lagging(FY)
        else:
            self.lines[line].update({
                page: opage(message, FX, MX, WX, FY)
            })


    def updatesched(self, sched, pages='', active=True, start='', end=''):
        '''Update the schedule or create one

        If the page does not exist it will create one with default settings

        Paramaters
        -------
        sched: string
            The schedule identifier
        pages: string
            The pages to be displayed when schedule active.
        active: bool, default=True
            Whether the schedule will be active.
        '''

        if sched not in self.schedules and pages != '' and active != False:
            # create the schedule
            self.schedules.update({
                sched: oschedule(pages, start, end)
            })
        else:
            self.schedules[sched].activate(active)
            if pages != '':
                o = self.schedules[sched]
                o.pages(pages)
                o.start(start)
                o.end(end)

    def getline(self, page, line='1'):
        if(line in self.lines and page in self.lines[line]):
            return self.lines[line][page]

    def show(self):
        """Show the Configuration"""
        for linenum, line in  sorted(self.lines.items()):
            print('### LINE ' + linenum + ' ###')
            for pagenum, page in line.items():
                m = 'M ' if page.changed else '  '
                print(m + '(' + pagenum + ') ' + page.packet())
        print('### SCHEDULES ###')
        for schednum, sched in sorted(self.schedules.items()):
            a = 'A ' if sched.active else 'N '
            m = 'M ' if sched.changed else '  '
            print( m + a + '(' + schednum + ') ' + sched.packet())

    def pushchanges(self, reset=False):
        """ Push the changes to the display

        Return
        ------
        bool
            True on success, False on failue
        """
        changes = 0
        changed = 0

        # reset display if requested
        if reset: self.send('<D*>')

        # begin update (turn the display off)
        self.send("<BE>")
        sleep(0.1)

        # update pages
        for linenum, line in  self.lines.items():
            for pagenum, page in sorted(line.items()):
                if page.modified(False) or reset:
                    changes += 1
                    if self.send('<L' + linenum + '><P' + pagenum + '>' + page.packet()):
                        logging.info("page " + pagenum + " OK - " + page.MM)
                        changed += 1
                    else:
                        logging.info("Page " + pagenum + " Failed - " + page.MM)
                else:
                    logging.info("Page " + pagenum + " Not Changed - " + page.MM)

        # update schedules
        for schednum, sched in self.schedules.items():
            if sched.modified(False) or reset:
                changes += 1
                if sched.active:
                    if self.send('<T' + schednum + '>' + sched.packet()):
                        logging.info("Sched " + schednum + " OK - " + sched.PP)
                        changed += 1
                    else:
                        logging.info("Schedule " + schednum + " Failed - " + sched.PP)
                else:
                    if self.send("<DT" + schednum  + ">"):
                        logging.info("Sched " + schednum + " OK - Deletion")
                        changed += 1
                    else:
                        logging.info("Schedule " + schednum + " Failed - Deletion")
            else:
                logging.info("Schedule " + schednum + " Not Changed - " + sched.PP)

        # end update
        sleep(0.1)
        self.send("<BF>")

        # check result
        if changes != changed:
            logging.info('There was some issue with the loading of changes')

        # save the new display config
        if changed > 0:
            logging.info('Changes Pushed')
            self.confput()

    def defaultrunpage(self, page=''):
        """The default page to display if no schedules are ser"""
        if len(page) == 1 and page in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            self.defaultPage = page
            if self.send("<RP" +self.defaultPage + ">"):
                logging.info("Default Run Page " + self.defaultPage + " set - OK")
            else:
                logging.info("Default Run Page " + self.defaultPage + " set - Failed")
        return self.defaultPage

    def setclock(self):
        """Will set the RTC on the display to localtime

        Return
        ------
        bool:
            true on success
        """
        if self.send(strftime("<SC>%y0%w%m%d%H%M%S", localtime())):
            logging.info("RTC set - OK")
        else:
            logging.info("RTC set - Failed")

    def brightness(self, bn='D'):
        """Modify the brightness of the screen

        Parameter
        ------
        bn: character, default='D'
        'A' = 100%
        'B' = 75%
        'C' = 50%
        'D' = 25%

        Return
        ------
        bool:
            true on success
        """
        if len(bn) == 1 and bn in 'ABCD':
            if self.send('<B' + bn + '>' ):
                logging.info("Brightness set - OK")
            else:
                logging.info("Brightness set - Failed")
        else:
            print("Invalid brightness")

        return self.response()

    def setid(self, newid):
        """Will set the ID on the display

        Return
        ------
        bool:
            true on success
        """
        data = "<ID><%02d><E>" % int(newid)
        logging.info("Send: " + data)
        self.ser.write(bytes(data, 'ASCII'))
        if self.response(expected="%02d" % int(newid)):
            logging.info("ID set - OK")
        else:
            logging.info("ID set - Failed")

    def getcolorbyte(self, colorChar):
        """Helper function for programgraphic()

        Paramaters
        -------
        colorChar: string
            The char from the graphic input string

        Return
        ------
        byte:
            the corresponding color byte
        """
        if  (colorChar == 'A'): return 0b10000000
        elif(colorChar == 'D'): return 0b01000000
        elif(colorChar == 'E'): return 0b11000000
        else: return 0b00000000

    def programgraphic(self, graphicid, blockid, graphiccontent):
        """Will program a graphic to the display

        Paramaters
        -------
        graphicid: string
            The graphic identifier (this graphic will be overridden on device)
        graphiccontent: string
            The graphic itself, represented as a string. Each char represents one pixel.
            Valid chars are: A = red, D = green, E = yellow, @ = off
            Please have a look at the sample graphic text file.

        Return
        ------
        bool:
            true on success
        """
        # check graphic and block parameter
        if(not graphicid in "ABCDEFGHIJKLMNOP" or not blockid in "12345678"):
            logging.info("Invalid graphic or block id - abort!")
            return

        # default data of one graphic (= 4 chars/blocks)
        # 0b10 = red, 0b01 = green, 0b11 = yellow, 0b00 = off
        data = [
            # block 1 (8x8 px)
            0xff,0xff, # 2 bytes represents 8 px
            0x00,0x00,
            0x00,0x00,
            0x00,0x00,
            0x00,0x00,
            0x00,0x00,
            0x00,0x00,
            0x00,0x00,
            # block 2 (right of prev block)
            0x00,0x00,
            0x00,0x00,
            0x00,0x00,
            0x00,0x00,
            0x00,0x00,
            0x00,0x00,
            0x00,0x00,
            0x00,0x00,
            # block 3 (right of prev block)
            0x00,0x00,
            0x00,0x00,
            0x00,0x00,
            0x00,0x00,
            0x00,0x00,
            0x00,0x00,
            0x00,0x00,
            0x00,0x00,
            # block 4 (right of prev block)
            0x00,0x00,
            0x00,0x00,
            0x00,0x00,
            0x00,0x00,
            0x00,0x00,
            0x00,0x00,
            0x00,0x00,
            0x00,0x00
        ]

        # parse graphic string
        graphiccontent = graphiccontent.splitlines()
        charoffset = 0
        block = 0
        blockok = True
        for block in [0,1,2,3,4,5,6,7]:
            for line in [0,1,2,3,4,5,6]:
                # check if enough data is avail for next block
                if(charoffset+7 >= len(graphiccontent[line])):
                    blockok = False
                    break
            # parse block if block is ok
            if(blockok):
                for line in [0,1,2,3,4,5,6]:
                    #print(graphiccontent[line][charoffset+0:charoffset+8])
                    chunk = 0x00
                    chunk2 = 0x00
                    for char in [0,1,2,3]:
                        chunk |= self.getcolorbyte(graphiccontent[line][charoffset+char]) >> (char*2)
                    for char in [0,1,2,3]:
                        chunk2 |= self.getcolorbyte(graphiccontent[line][charoffset+char+4]) >> (char*2)
                    data[(block*16)+(line*2)+0] = chunk
                    data[(block*16)+(line*2)+1] = chunk2
                # set next block begin
                charoffset += 8
                block += 1

        # convert byte array to string for send() function
        packet = ""
        for d in data: packet += chr(d)

        # send payload
        self.send("<G"+graphicid+blockid+">"+packet)

    def send(self, packet):
        """Send the packet to the display and return the response

        Parameters
        ------
        packet: string
            The packet to send to the display

        Return
        ------
        bool:
            from the self.response function
        """
        # append device ID and end tag
        payload = '<ID%02x>' % self.device + packet + self.chsum(packet) + '<E>'

        # correct conversion for binary data (graphics)
        data = []
        for char in payload: data.append(ord(char))
        data = bytes(data)

        # send
        logging.info('Send: ' + payload)
        logging.info('Send bytes: ' + ":".join("{:02x}".format(c) for c in data))
        self.ser.write(data)
        return self.response()

    def response(self, expected='ACK'):
        """ Get the response from the display
        Note: There is no ACK response using Sign ID=00

        Return
        ------
        bool:
            true on success
        """
        if(self.device == 0):
            return True

        out = ''
        sleep(1)
        while self.ser.inWaiting() > 0:
            out += self.ser.read(1).decode('ASCII')
        logging.info('Response: ' + out)
        if out != '':
            if out == expected:
                return True
            else:
                return False
