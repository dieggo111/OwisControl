# coding=utf-8
import serial
import time
import sys, os
import OwisError



class owis:

    def __init__(self, port1=None, port2=None, port3=None):

        self.logPath = os.getcwd()
        # front slash for linux :)
        self.logName = "/Logfile.txt"
        self.serial_nr = ["08070255","08070256","08070257"]
        self.serList = []

        # x_max is about 20000um = 1000000 ink
        self.xRange = 1000000
        # x_max is about 20000um = 1000000 ink
        self.yRange = 1000000
        # z_max is about 12000um = 600000 ink
        self.zRange = 600000

        self.xSteps = 50
        self.ySteps = 50
        self.zSteps = 50

        self.zDrive = None

        self.port1 = port1
        self.port2 = port2
        self.port3 = port3

        # default parameters for serial port
        self.baudrate = 9600
        self.bytesize = 8
        self.timeout = 0.14


    def init(self):
        """ The PS10 controller is only able to control one motor. As a
        consequence you need to create 3 serial objects to control a xyz-stage.
        These objects are stored in the 'self.serList' list.
        """

        try:
            if self.port1 is not None:
                self.ser1 = serial.Serial(port=self.port1,
                                          baudrate=self.baudrate,
                                          bytesize=self.bytesize,
                                          timeout=self.timeout)
                self.serList.append(self.ser1)
            else:
                self.serList.append(None)

            if self.port2 is not None:
                self.ser2 = serial.Serial(port=self.port2,
                                          baudrate=self.baudrate,
                                          bytesize=self.bytesize,
                                          timeout=self.timeout)
                self.serList.append(self.ser2)
            else:
                self.serList.append(None)

            if self.port3 is not None:
                self.ser3 = serial.Serial(port=self.port3,
                                          baudrate=self.baudrate,
                                          bytesize=self.bytesize,
                                          timeout=self.timeout)
                self.serList.append(self.ser3)
            else:
                self.serList.append(None)

            if self.port1 is None and self.port2 is None and self.port3 is None:
                raise ValueError("No port information given")
            else:
                pass

            print("Initializing...")

            # initialize x, y, z-axis with saved default parameters
            for i in range(1, 4):
                if self.serList[i-1] is not None:
                    self.serList[i-1].write(b"INIT1\r\n")
                else:
                    pass

        except:
            raise OwisError.ComError("Comport is already claimed or can not be found!")

        # set terminal mode to '0' (short answer)
        # controller that was set to 'TERM=2' will send one last 'OK'
        for i in range(1, 4):
            if self.serList[i-1] is not None:
                self.serList[i-1].write(b"TERM=0\r\n")
                self.serList[i-1].readline().decode("utf-8")
            else:
                pass

        # set position format to 'absolute'
        for i in range(1, 4):
            if self.serList[i-1] is not None:
                self.serList[i-1].write(b"ABSOL1\r\n")
            else:
                pass

        # set axis order
        self.PS10_idnAxis()

        return True


########################
# check/status methods #
########################


    def checkInit(self):

        # request current motor position (no display here)
        self.curPos = [None,None,None]
        for i in range(1, 4):
            if self.serList[i-1] is not None:
                self.serList[i-1].write(b"?CNT1\r\n")
                self.curPos[i-1] = self.serList[i-1].readline().decode("utf-8").replace("\r","")
            else:
                pass

        for val in self.curPos:
            # check if serial-timeout is sufficient
            if val == "":
                raise OwisError.ComError("Could not get proper position information in time!")
            #check if current position is in the expected range
            elif val != None and int(val) < 0:
                print("Warning: Unexpected axis positions. Motor needs to be calibrated!")
                # raise OwisError.SynchError("Unexpected axis positions. Motor needs to be calibrated!")
            else:
                pass

        # print("Current position in (ink) [x, y, z]: " \
        #       + str(self.curPos).replace("'",""))
        print("Current position in (um) [x, y, z]: [" \
              + self.getPos("str") + "]")

        return True


    def checkLog(self):

        # create logfile if it isn't there
        if os.path.isfile(self.logPath + self.logName) is False:
            self.writeLog()
            print("Created new Logfile...")
        # check if motor position and log position are equal
        elif self.readLog() is False:
            print("Warning: Display counter and motor position are unequal.")
            # raise OwisError.SynchError("Motor position and position from log file are unequal!")
        else:
            return True


    def checkStatus(self, mode="print"):
        """ Checks and prints axis and position status if
        'mode' argument is 'True'. A 'True' value is returned as soon as
        movement is finished.

        """

        status = [None,None,None]

        while True:
            for i in range(1, 4):
                if self.serList[i-1] is not None:
                    self.serList[i-1].write(b"?ASTAT\r\n")
                    status[i-1] = self.serList[i-1].readline().decode("utf-8").replace("\r","")
                else:
                    pass

            if mode == "print":
                self.printAll(status)
            else:
                pass

            if status == ["R", "R", "R"]:
                return True
                break

            # in case a motor is still tapping a limit switch
            elif "L" in status:
                i = status.index("L")
                self.freeMotor(i)
                return False
            else:
                return False


    def checkRange(self, x, y, z):
        """ Checks if new position is within the accepted range according to
        the 'self.(x,y,z)Range' values. Only absolute values can be checked.
        Method expects arguments to be in [um].

        """

        checkList = [int(x),int(y),int(z)]
        rangeList = [self.xRange,self.yRange,self.zRange]

        if (checkList[0] not in range(0, self.xRange+1))\
        or (checkList[1] not in range(0, self.yRange+1))\
        or (checkList[2] not in range(0, self.zRange+1)):
            raise OwisError.MotorError("Destination is out of motor range!")
        else:
            pass

        return True


    def getPos(self, mode = None):
        """ Returns a string that contains the current axis positions (x,y,z)
        in [um]. The ink values of 'self.curPos'are preserved. The 'mode'
        argument is used the return a formated string.

        """

        if mode is "str":
            curPos = self.ink_to_len(self.curPos)
            return curPos[0] + "," + curPos[1] + "," + curPos[2]
        else:
            return self.ink_to_len(self.curPos)

        return True


    def getStatus(self):
        """ Returns current axis status.

        """

        status = []

        for i in range(1, 4):
            if self.serList[i-1] is not None:
                self.serList[i-1].write(b"?ASTAT\r\n")
                status.append(self.serList[i-1].readline().decode("utf-8").replace("\r",""))
            else:
                pass

        status = str(status).replace("[","").replace("]","").replace("'","").replace(" ","")

        return status


    def printAll(self, status):
        """ Prints current axis status and current position.

        """

        tempPos = [None,None,None]

        for i in range(1, 4):
            if self.serList[i-1] is not None:
                self.serList[i-1].write(b"?CNT1\r\n")
                tempPos[i-1] = self.serList[i-1].readline().decode("utf-8").replace("\r","")
            else:
                pass

        print("status = " + str(status) + " ; position = " + str(self.ink_to_len(tempPos)))

        return True


#######################
# PS 10 motor methods #
#######################


    def PS10_idnAxis(self):
        """ If you connect several PS10 controllers, the the port adresses are
        assigned arbitrarily. To make sure that a certain controller is always
        assigned to x-, y- or z-motor, you need to check their serials.
        The serial numbers are stored in 'self.serial_nr' and the serial
        objects in 'self.serList' are then ordered accordingly.
        """

        idnList = []
        tempList = [None,None,None]
        unknownList = []

        # get all serials
        for ser in self.serList:
            if ser is not None:
                ser.write(b"?SERNUM\r\n")
                idnList.append(ser.readline().decode("utf-8").replace("\r",""))
            else:
                pass

        # serial objects are ordered
        for i, idn in enumerate(idnList):
            if idn in self.serial_nr:
                if self.serial_nr.index(idn) is 0:
                    tempList[0] = self.serList[i]
                elif self.serial_nr.index(idn) is 1:
                    tempList[1] = self.serList[i]

                elif self.serial_nr.index(idn) is 2:
                    tempList[2] = self.serList[i]
            else:
                print("Unknown serial number: " + idn)
                unknownList.append(self.serList[i])

        # unkown controllers are assigned at the end
        for ser in unknownList:
            for i, temp in enumerate(tempList):
                if temp == None:
                    tempList[i] = ser

        self.serList = tempList

        return True


    def MOVA(self, x, y, z):
        """ Sends new position to controller and starts the movement. Position
        is written into logfile if run is succesfull.
        (x,y,z) arguments are considered as [um]. It is important to note
        that the controller expects [inkrement] values!

        Args:
        x,y,z : int or str (value in [um])

        """

        # check if movement is neccessary
        if [x, y, z] == self.ink_to_len(self.curPos):
            pass
        else:
            # convert [um] values into [ink]
            newPos = self.len_to_ink([x,y,z])

            # check if request is within boundaries
            self.checkRange(x, y, z)

            # send new destination to controller and start motor movement
            for i, val in enumerate(newPos):
                if val is not None:
                    self.serList[i].write(bytes("PSET1=" + newPos[i] + "\r\n","utf-8"))
                    self.serList[i].write(b"PGO1\r\n")
                else:
                    pass

            print("Moving to new position...")

            # status request: check current position and status until destination is reached
            while True:
                if self.checkStatus("print") == True:
                    break
                else:
                    pass

            # read-out final position
            for i, val in enumerate(newPos):
                if val is not None:
                    self.serList[i].write(b"?CNT1\r\n")
                    self.curPos[i] = self.serList[i].readline().decode("utf-8").replace("\r","")
                else:
                    pass

            # check if desired position was reached, print, update logfile
            if newPos != self.curPos:
                raise ValueError("Couldn't reach desired destination. Run failed...")
            else:
                print("New position [x, y, z]: " + str(self.ink_to_len(self.curPos)).replace("'",""))
                self.writeLog()

        return True


    def MOVR(self, x, y, z):

        """ New position is calculated according to the relative values given.
        Sends new position to controller and starts the movement. Position
        is written into logfile if run is succesfull.
        (x,y,z) arguments are considered as [um]. It is important to note
        that the controller expects [inkrement] values!

        Args:
        x,y,z : int or str (value in [um])

        """

        # convert relative into absolute positions
        newPos = [None,None,None]
        tempList = self.len_to_ink([x,y,z])
        for i, val in enumerate(self.curPos):
            if val is not None:
                newPos[i] = int(self.curPos[i]) + int(tempList[i])
            else:
                pass
        newPos = self.ink_to_len(newPos)
        # from here on it is basically an absolute movement
        self.MOVA(newPos[0],newPos[1],newPos[2])

        return True


    def REFDRIVE(self, mode=None):

        # set reference mask for x, y, z
        for i in range(1, 4):
            if self.serList[i-1] is not None and i < 3:
                # 1 = 0001 = MINSTOP
                # 2 = 0010 = MINDEC
                self.serList[i-1].write(b"RMK1=2\r\n")
            # old z-motor only has MINSTOP limit switch
            elif self.serList[i-1] is not None and i == 3:
                self.serList[i-1].write(b"RMK1=1\r\n")
            else:
                pass

        # set reference run velocity for x, y, z (std val = 4000)
        for i in range(1, 4):
            if self.serList[i-1] is not None:
                self.serList[i-1].write(b"RVELS1=1000\r\n")
            else:
                pass

        # set reference mode and start reference run for x, y, z
        if mode is not None:
            for i in range(1, 4):
                if self.serList[i-1] is not None:
                    self.serList[i-1].write(bytes("REF1=" + str(mode) + "\r\n","utf-8"))
                else:
                    pass
        else:
            for i in range(1, 4):
                if self.serList[i-1] is not None:
                    self.serList[i-1].write(b"REF1=4\r\n")
                else:
                    pass

        # status request: check current position and status until destination is reached
        while True:
            if self.checkStatus("print") == True:
                break
            else:
                pass

        print("Reference run finished...")

        # read-out final position
        for i in range(1, 4):
            if self.serList[i-1] is not None:
                self.serList[i-1].write(b"?CNT1\r\n")
                self.curPos[i-1] = self.serList[i-1].readline().decode("utf-8").replace("\r","")
            else:
                pass

        # check if desired position was reached, print, update logfile
        if self.curPos != ["0","0","0"]:
            raise ValueError("Couldn't reach desired destination. Run failed...")
        else:
            print("New position [x, y, z]: " + str(self.ink_to_len(self.curPos)).replace("'",""))
            self.writeLog()

        return True


    def motorOff(self):

        # turn x, y, z-motor off
        for i in range(1, 4):
            if self.serList[i-1] is not None:
                self.serList[i-1].write(b"MOFF1\r\n")
            else:
                pass

        print("Motors are off...")

        return True


    def freeMotor(self, index):
        """ In case a motor is still sitting on a limit switch, this motor
        needs to be released to be able to operate again.

        """

        self.serList[index].write(b"INIT1\r\n")
        time.sleep(0.5)
        self.serList[index].write(b"EFREE1\r\n")
        time.sleep(2)

        return True


######################
# conversion methods #
######################


    def ink_to_len(self, posList):
        """ Converts list values from [inkrement] into [um]. The new values are
        calculated according to the micro steps of the motor.

        """

        temp = []

        for el in posList:
            if el == "" or el == None:
                temp.append(0)
            else:
                temp.append(float(el))


        temp[0] = str(int(temp[0]/self.xSteps))
        temp[1] = str(int(temp[1]/self.ySteps))
        temp[2] = str(int(temp[2]/self.zSteps))

        return temp


    def len_to_ink(self, posList):
        """ Converts list values from [um] into [inkrement]. The new values are
        calculated according to the micro steps of the motor.

        """

        temp = []

        for el in posList:
            if el == "" or el == None:
                temp.append(0)
            else:
                temp.append(float(el))

        temp[0] = str(int(temp[0]*self.xSteps))
        temp[1] = str(int(temp[1]*self.ySteps))
        temp[2] = str(int(temp[2]*self.zSteps))

        return temp



###############
# log methods #
###############


    def writeLog(self):
        """ Converts current position into [um] and writes it into a log file.

        """

        temp = self.ink_to_len(self.curPos)

        with open(self.logPath + self.logName, "w") as File:
            File.write("{:>0}{:>20}{:>20}".format("x = " + temp[0] , "y = " + temp[1] , "z = " + temp[2]))

        print("Current position saved in Logfile...")

        return True


    def readLog(self):
        """ Reads log position and compares it with cuurent position.

        """

        logPos = []

        with open(self.logPath + self.logName, "r") as File:
            line = File.readline().split()
            logPos.append(line[2])
            logPos.append(line[5])
            logPos.append(line[8])
        print(self.curPos, self.len_to_ink(logPos))
        if self.curPos != self.len_to_ink(logPos):
            return False
        else:
            return True


################
# test methods #
################


    # def test_drive(self, Filename):
    #
    #     z = self.curPos[2]
    #     path = os.getcwd()
    #
    #     print("Start test drive according to " + Filename[1:])
    #     with open(path + Filename, "r") as File:
    #         for line in File:
    #             try:
    #                 (x,y) = line.split()
    #                 self.probe_moveAbs(int(x)*self.xSteps,int(y)*self.xSteps,z)
    #             except:
    #                 pass
    #
    #     return True


    def test(self, axis=None):

        if axis == None or axis == 0:
            controller = "x"
        elif axis == 1:
            controller = "y"
        elif axis == 2:
            controller = "z"
        else:
            raise ValueError("Unkown argument.")

        print("###############################################################")
        print("Test function started. Ready to send commands "
              "to %s-controller." %controller)
        print("Table of commands: http://www.owis.eu/fileadmin/_migrated/content_uploads/PS_10_Betriebsanleitung_2014.pdf")
        print("Type 'q' to exit and turn off motor.")

        while True:
            cmd = input("Enter command:")

            if cmd == "q":
                print("Test programm closed.")
                self.motorOff()
                break
            else:
                if axis == None:
                    self.serList[0].write(bytes(cmd + "\r\n", "utf-8"))
                    answer = self.serList[0].readline().decode("utf-8")
                else:
                    self.serList[axis].write(bytes(cmd + "\r\n", "utf-8"))
                    answer = self.serList[axis].readline().decode("utf-8")
                print(answer)

        return True






# main loop
if __name__=='__main__':


    try:

        o = owis(port1="/dev/ttyACM1", port2="/dev/ttyACM0", port3="/dev/ttyACM2")
        o.init()
        o.checkInit()
        # o.checkLog()
        # o.freeMotor()
        # for i in range(1, 5):
        #     o.MOVA(1000,1000,4000)
        #     time.sleep(2)
        #     o.REFDRIVE()
        # o.motorOff()
        # o.MOVA(15000,15000,7000)
        o.MOVR(1000,1000,0)
        # o.REFDRIVE()
        # o.test(0)





    except(KeyboardInterrupt):
        print()
        print("Run interrupted. Motors off.")
        o.motorOff()

##    o.check_zDrive()
##    o.test_drive("\Seedtest.txt")

    # o.writeLog()

#    print("Run time: " + str(time.time()-start))

## Stresstest mit CPUSTRESS.EXE
## 1%   CPU Auslastung : 91,6 s
## 75%  CPU Auslastung : 91,7 s
## 100% CPU Auslastung : 91,7 s
