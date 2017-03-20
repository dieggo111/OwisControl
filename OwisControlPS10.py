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

        self.xRange = 1040000
        self.yRange = 1040000
        self.zRange = 630000

        self.xSteps = 50
        self.ySteps = 50
        self.zSteps = 10000

        self.zDrive = None

        self.port1 = port1
        self.port2 = port2
        self.port3 = port3

        # default parameters for serial port
        self.baudrate = 9600
        self.bytesize = 8
        self.timeout = 0.12


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

        # # release motor from limit switches if neccessary
        # for i in range(1, 4):
        #     if self.serList[i-1] is not None:
        #         self.serList[i-1].write(b"?ASTAT\r\n")
        #         print(str(self.serList[i-1].readline().decode("utf-8")))
        #         if self.serList[i-1].readline().decode("utf-8") == "L":
        #             print("Release limit switch")
        #             self.serList[i-1].write(b"EFREE1\r\n")
        #         else:
        #             pass
        #     else:
        #         pass

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

        # check if serial-timeout is sufficient
        for val in self.curPos:
            if val == "":
                raise OwisError.ComError("Could not get proper position information in time!")
            # check if current position is in the expected range
                # elif val != None and int(val) < 0:
                    # raise OwisError.SynchError("Unexpected axis positions. Motor needs to be calibrated!")
            else:
                pass

            # # create logfile if it isn't there
            # if os.path.isfile(self.logPath + self.logName) is False:
            #     self.writeLog()
            #     print("Created new Logfile...")
            # # check if motor position and log position are equal
            # elif self.readLog() is False:
            #     raise OwisError.SynchError("Motor position and position from log file are unequal!")
            # else:
            #     pass

        print("Current position in (ink) [x, y, z]: " \
              + str(self.curPos).replace("'",""))
        print("Current position in (um) [x, y, z]: [" \
              + self.getPos("str") + "]")

        return True


    def checkStatus(self):

        status = [None,None,None]
        motor_status = False

        while True:
            for i in range(1, 4):
                if self.serList[i-1] is not None:
                    self.serList[i-1].write(b"?ASTAT\r\n")
                    status[i-1] = self.serList[i-1].readline().decode("utf-8").replace("\r","")
                else:
                    pass

            print("status = ", status)

            if "L" in status[0]:
                self.motorRelease("x")
                print("Releasing x-motor from limit switch.")
                motor_status = "restart"
                break
            elif "L" in status[1]:
                self.motorRelease("y")
                print("Releasing y-motor from limit switch.")
                motor_status = "restart"
                break
            elif "L" in status[2]:
                self.motorRelease("z")
                print("Releasing z-motor from limit switch.")
                motor_status = "restart"
                break
            elif status == ["R", "R", "R"]:
                motor_status = True
                break
            else:
                pass

        return motor_status


    def checkRange(self, x, y, z, mode):

        x = int(x)
        y = int(y)
        z = int(z)

        checkList = [int(x),int(y),int(z)]
        rangeList = [self.xRange,self.yRange,self.zRange]

        if mode == "Abs":
            if x not in range(0, self.xRange+1) or y not in range(0, self.yRange+1) or z not in range(0, self.zRange+1):
                raise OwisError.MotorError("Destination is out of motor range!")
            else:
                pass

        elif mode == "Rel":
            for i, val in enumerate(self.curPos):
                if val is not None:
                    if int(val)+checkList[i] not in range(0, rangeList[i]+1):
                        raise OwisError.MotorError("Destination is out of motor range!")
                    else:
                        pass
                else:
                    pass

#            if (int(self.curPos[0])+x) not in range(0, self.xRange+1) or(int(self.curPos[1])+y) not in range(0, self.yRange+1) or (int(self.curPos[2])+z) not in range(0, self.zRange+1):
#                raise OwisError.MotorError("Destination is out of motor range!")
#            else:
#                pass
        else:
            raise ValueError("Unknown movement mode! Try 'Abs' or 'Rel'.")

        return True


    def getPos(self, mode = None):
        """ Returns a string of a list of strings (x,y,z) of the current
        position.

        """

        if mode is "str":
            curPos = self.ink_to_len(self.curPos)
            return curPos[0] + "," + curPos[1] + "," + curPos[2]
        else:
            return self.ink_to_len(self.curPos)



    def printStatus(self, posList, status):
        """ Prints current axis status and current position.

        """

        tempPos = [None,None,None]
        for i, val in enumerate(posList):
            for i in range(1, 4):
                if self.serList[i-1] is not None:
                    self.serList[i-1].write(b"?CNT1\r\n")
                    tempPos[i-1] = self.serList[i-1].readline().decode("utf-8").replace("\r","")
                else:
                    pass

        print("status = " + str(status) + " ; position = " + str(tempPos))


        return True



#######################
# PS 10 motor methods #
#######################


    def PS10_idnAxis(self):
        """ PS10s come in a set of 3 controllers. They are assigned to x-, y-,
        z- motor in respect to their serial number. The serial numbers are
        stored in 'self.serial_nr' and the serial objects in 'self.serList'
        are then ordered accordingly.
        """

        idnList = []
        tempList = [None,None,None]
        for ser in self.serList:
            if ser is not None:
                ser.write(b"?SERNUM\r\n")
                idnList.append(ser.readline().decode("utf-8").replace("\r",""))
            else:
                pass

        for i, ser in enumerate(idnList):
            if self.serial_nr.index(ser) is 0:
                tempList[0] = self.serList[i]
            elif self.serial_nr.index(ser) is 1:
                tempList[1] = self.serList[i]
            elif self.serial_nr.index(ser) is 2:
                tempList[2] = self.serList[i]

        self.serList = tempList

        return True


    def MOVR(self, x, y, z):

        # check if request is within boundaries
        self.checkRange(x, y, z, "Rel")

        newPos = [None,None,None]
        tempList = [int(x),int(y),int(z)]
        for i, val in enumerate(self.curPos):
            if val is not None:
                newPos[i] = str(int(self.curPos[i]) + tempList[i])
            else:
                pass

        # send new destination to controller and start motor movement
        for i, val in enumerate(newPos):
            if val is not None:
                self.serList[i].write(bytes("PSET1=" + newPos[i] + "\r\n","utf-8"))
                self.serList[i].write(b"PGO1\r\n")
            else:
                pass

        print("Moving to new position...")

        # status request: check current position until destination is reached
        self.printPos(newPos)

        # print current destination
        for i, val in enumerate(newPos):
            if val is not None:
                self.serList[i].write(b"?CNT1\r\n")
                self.curPos[i] = self.serList[i].readline().decode("utf-8").replace("\r","")
            else:
                pass

        print("New position [x, y, z]: " + str(self.curPos).replace("'",""))

        return True


    def MOVA(self, x, y, z):

        # check if request is within boundaries
        self.checkRange(x, y, z, "Abs")

        newPos = [str(x), str(y), str(z)]

        # send new destination to controller and start motor movement

        for i, val in enumerate(newPos):
            if val is not None:
                self.serList[i].write(bytes("PSET1=" + newPos[i] + "\r\n","utf-8"))
                self.serList[i].write(b"PGO1\r\n")
                self.serList[i].write(b"?ASTAT\r\n")
                if self.serList[i].readline().decode("utf-8").replace("\r","") == "L":
                    print("test" + str(i))
                    self.motorRelease(i)
                    self.serList[i].write(bytes("CNT1=0\r\n","utf-8"))
                    self.serList[i].write(bytes("PSET1=" + newPos[i] + "\r\n","utf-8"))
                    self.serList[i].write(b"PGO1\r\n")
            else:
                pass


        print("Moving to new position...")

        # status request: check current position and status until destination is reached
        status = [None,None,None]
        while True:
            for i in range(1, 4):
                if self.serList[i-1] is not None:
                    self.serList[i-1].write(b"?ASTAT\r\n")
                    status[i-1] = self.serList[i-1].readline().decode("utf-8").replace("\r","")
                else:
                    pass

            self.printStatus(newPos, status)

            # if "L" in status[0]:
            #     self.motorRelease("x")
            #     print("Releasing x-motor from limit switch.")
            #     break
            # elif "L" in status[1]:
            #     self.motorRelease("y")
            #     print("Releasing y-motor from limit switch.")
            #     motor_status = "restart"
            #     break
            # elif "L" in status[2]:
            #     self.motorRelease("z")
            #     print("Releasing z-motor from limit switch.")
            #     motor_status = "restart"
            #     break
            if status == ["R", "R", "R"]:
                break
            else:
                pass

        # print final destination
        for i, val in enumerate(newPos):
            if val is not None:
                self.serList[i].write(b"?CNT1\r\n")
                self.curPos[i] = self.serList[i].readline().decode("utf-8").replace("\r","")
            else:
                pass

        if newPos != self.curPos:
            raise ValueError("Run failed...")
        else:
            print("New position [x, y, z]: " + str(self.curPos).replace("'",""))

        return True


    def ref(self):

        # set reference mask for x, y, z
        for i in range(1, 4):
            if self.serList[i-1] is not None:
                # 2 = 0010 = MINDEC
                self.serList[i-1].write(b"RMK1=2\r\n")
            else:
                pass

        # set reference run velocity for x, y, z (std val = 41943)
        for i in range(1, 4):
            if self.serList[i-1] is not None:
                self.serList[i-1].write(b"RVELS1=1000\r\n")
            else:
                pass

        # set reference mode and start reference run for x, y, z
        for i in range(1, 4):
            if self.serList[i-1] is not None:
                self.serList[i-1].write(b"REF1=4\r\n")
            else:
                pass

        while True:
            for i in range(1, 4):
                if self.serList[i-1] is not None:
                    self.serList[i-1].write(b"?ASTAT\r\n")
                    status[i-1] = self.serList[i-1].readline().decode("utf-8").replace("\r","")
                else:
                    pass

            print("status = ", status)

            if "L" in status:
                print("L in status")
            # if "L" in status[0]:
            #     self.motorRelease("x")
            #     print("Releasing x-motor from limit switch.")
            #     break
            # elif "L" in status[1]:
            #     self.motorRelease("y")
            #     print("Releasing y-motor from limit switch.")
            #     motor_status = "restart"
            #     break
            # elif "L" in status[2]:
            #     self.motorRelease("z")
            #     print("Releasing z-motor from limit switch.")
            #     motor_status = "restart"
            #     break
            elif status == ["R", "R", "R"]:
                break
            else:
                pass

        # REF1=4 doesnt seem to work, so this needs to be done 'by hand'
        # for i in range(1, 4):
        #     self.serList[i-1].write(b"CNT1=0\r\n")
        # print final destination
        print("Reference run finished...")

        for i in range(1, 4):
            if self.serList[i-1] is not None:
                self.serList[i-1].write(b"?CNT1\r\n")
                self.curPos[i-1] = self.serList[i-1].readline().decode("utf-8").replace("\r","")
            else:
                pass

        print("New position [x, y, z]: " + str(self.curPos).replace("'",""))


        return True


    def motorRelease(self, motor=None):

        if motor is None:
            for i in range(1, 4):
                if self.serList[i-1] is not None:
                    self.serList[i-1].write(b"INIT1\r\n")
                    time.sleep(0.2)
                    self.serList[i-1].write(b"EFREE1\r\n")
                    time.sleep(1)
                else:
                    pass
        elif motor is 0:
            self.serList[0].write(b"INIT1\r\n")
            time.sleep(0.2)
            self.serList[0].write(b"EFREE1\r\n")
            time.sleep(0.2)
        elif motor is 1:
            self.serList[1].write(b"INIT1\r\n")
            print("sleep" + str(motor))
            time.sleep(0.2)
            self.serList[1].write(b"EFREE1\r\n")
            time.sleep(0.2)
        elif motor is 2:
            self.serList[2].write(b"INIT1\r\n")
            time.sleep(0.2)
            self.serList[2].write(b"EFREE1\r\n")
            time.sleep(0.2)

        else:
            raise ValueError("Unknown parameter.")

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



######################
# conversion methods #
######################


    def ink_to_len(self, posList):
        """ Converts [inkrements] into [um]. Elements of a position list are
        converted into integers first. Then, the new values are calculated
        according to the micro steps of the motor. The values of the
        original list ought not to be changed.

        """

        temp1 = []
        temp2 = []

        for el in posList:
            temp1.append(int(el))

        temp2.append(str(int(temp1[0]/self.xSteps)))
        temp2.append(str(int(temp1[1]/self.ySteps)))
        temp2.append(str(int(temp1[2]/self.zSteps)))

        return temp2


    def len_to_ink(self, posList):

        temp1 = []
        temp2 = []
        print(len(temp2))
        for el in posList:
            temp1.append(int(el))

        temp2.append(str(int(temp1[0]*self.xSteps)))
        temp2.append(str(int(temp1[1]*self.ySteps)))
        temp2.append(str(int(temp1[2]*self.zSteps)))

        return temp2



###############
# log methods #
###############


    def writeLog(self):

        with open(self.logPath + self.logName, "w") as File:
            File.write("{:>0}{:>20}{:>20}".format("x = " + self.curPos[0] , "y = " + self.curPos[1] , "z = " + self.curPos[2]))

        print("Current position saved in Logfile...")

        return True


    def readLog(self):

        logPos = []

        with open(self.logPath + self.logName, "r") as File:
            line = File.readline().split()
            logPos.append(line[2])
            logPos.append(line[5])
            logPos.append(line[8])

        if self.curPos != logPos:
            return False

#        for i in range(1, 4):
#            self.ser.write(b"DISPCNT" + str(i) + "=" + self.curPos[i-1] + "\r\n")
#            self.ser.write(b"CNT" + str(i) + "=" + self.curPos[i-1] + "\r\n")
#
#        print("Recent position coordinates were sent to controler ...")
#        print("Current position [x, y, z]: " + str(self.curPos).replace("'",""))

        else:
            return True



################
# test methods #
################


    def test_drive(self, Filename):

        z = self.curPos[2]
        path = os.getcwd()

        print("Start test drive according to " + Filename[1:])
        with open(path + Filename, "r") as File:
            for line in File:
                try:
                    (x,y) = line.split()
                    self.probe_moveAbs(int(x)*self.xSteps,int(y)*self.xSteps,z)
                except:
                    pass

        return True


    def test(self, axis=None):

        while True:
            cmd = input("Enter command:")

            if cmd == "q":
                print("Test programm closed.")
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

        o = owis(port1="/dev/ttyACM0", port2="/dev/ttyACM2", port3="/dev/ttyACM1")
        o.init()
        o.checkInit()

        o.MOVA(100000,100000,0)
        # o.MOVR(0,10000,0)
        # o.ref()
        # o.test(0)


    except(KeyboardInterrupt):
        print()
        print("Run interrupted.")
        o.motorOff()

##    o.check_zDrive()
##    o.test_drive("\Seedtest.txt")

    # o.writeLog()

#    print("Run time: " + str(time.time()-start))

## Stresstest mit CPUSTRESS.EXE
## 1%   CPU Auslastung : 91,6 s
## 75%  CPU Auslastung : 91,7 s
## 100% CPU Auslastung : 91,7 s

# (*1):
        # set denominator of conversion factor for position calculation
        # default val: x = 10000 = 1mm, y = 10000 = 1mm, z = 50000 = 1mm
#        for i in range(1, 3):
#            self.ser.write(b"WMSFAKN" + str(i) + "=10000\r\n")
#        self.ser.write(b"WMSFAKN3=50000\r\n")
#        # set motor type (3 = Schrittmotor Closed-Loop)
#        self.ser.write(b"MOTYPE3\r\n")
#        # set current range (Strombereich) for x, y, z (0 = low)
#        for i in range(1, 4):
#            self.ser.write(b"AMPSHNT" + str(i) + "=0\r\n")
#        # set end switch mask (Endschaltermaske) for x, y, z
#        for i in range(1, 4):
#            self.ser.write(b"SMK" + str(i) + "=0110\r\n")
