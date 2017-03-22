# coding=utf-8
import serial
import time
import sys, os
import OwisError



class owis:

    def __init__(self, port1=None, port2=None, port3=None):



        self.model = "PS35"
        self.logPath = os.getcwd()
        # back slash for windows :(
        self.logName = "\Logfile.txt"

        self.xRange = 1400000
        self.yRange = 1400000
        self.zRange = 600000

        self.xSteps = 10000
        self.ySteps = 10000
        self.zSteps = 50000

        self.zDrive = 50000

        if port1 == None:
            self.port1 = "COM5"
        else:
            self.port1 = port1


        # default parameters for serial port
        self.baudrate = 9600
        self.bytesize = 8
        self.timeout = 0.12


    def init(self):


        try:
            self.ser = serial.Serial(port=self.port1,
                            baudrate=self.baudrate,
                            bytesize=self.bytesize,
                            timeout=self.timeout)

            print("Initializing...")

# (*1)

            # initialize x, y, z-axis with saved default parameters
            for i in range(1, 4):
                self.ser.write(bytes("INIT" + str(i) + "\r\n"), "utf-8")

        except:
            raise OwisError.ComError("Comport is already claimed or can not be found!")


            # set terminal mode to '0' (short answer)
            # controller that was set to 'TERM=2' will send one last 'OK'
            for i in range(1, 4):
                self.ser.write(b"TERM=0\r\n")
                self.ser.readline().decode("utf-8")

            # set position format to 'absolute'
            for i in range(1, 4):
                self.ser.write(bytes("ABSOL" + str(i) + "\r\n"), "utf-8")

            # set position format to 'absolute'
            for i in range(1, 4):
                self.ser.write(bytes("ABSOL" + str(i) + "\r\n"), "utf-8")

        return True


########################
# check/status methods #
########################


    def checkInit(self):


        # request current motor position and display values
        self.curPos = []
        display_counter = []
        for i in range(1, 4):
            self.ser.write(bytes("?CNT" + str(i) + "\r\n"), "utf-8")
            self.curPos.append(self.ser.readline().decode("utf-8").replace("\r",""))
            self.ser.write(bytes("?DISPCNT" + str(i) + "\r\n"), "utf-8")
            display_counter.append(self.ser.readline().decode("utf-8").replace("\r",""))

        # check if serial-timeout is sufficient
        for val in self.curPos:
            if val == "":
                raise OwisError.ComError("Could not get proper position information in time!")
        # check if current position is in the expected range
            elif val != None and int(val) < 0:
                raise OwisError.SynchError("Unexpected axis positions. Motor needs to be calibrated!")
            else:
                pass

        # check if display counter and motor position are equal
        if display_counter != self.curPos:
            raise OwisError.SynchError("Display counter and motor position are unequal!")
        # check if motor position and log position are equal
        elif self.readLog() is False:
            raise OwisError.SynchError("Motor position and position from log file are unequal!")
        else:
            print("Current position [x, y, z]: " + str(self.curPos).replace("'",""))


        # # create logfile if it isn't there
        # if os.path.isfile(self.logPath + self.logName) is False:
        #     self.writeLog()
        #     print("Created new Logfile...")
        # # check if motor position and log position are equal
        # elif self.readLog() is False:
        #     raise OwisError.SynchError("Motor position and position from log file are unequal!")
        # else:
        #     pass

        print("Current position in (ink) [x, y, z]: " + str(self.curPos).replace("'",""))
        print("Current position in (um) [x, y, z]: [" + self.getPos("str") + "]")

        return True


    def checkStatus(self):

        while True:
            self.ser.write(b"?ASTAT" + "\r\n")
            status = self.ser.readline().decode("utf-8").replace("\r","")

            if "T" not in status:
                return True
                break
            else:
                pass


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



    def printPos(self, posList):

        # read-out temp position until requested position is reached

        while True:
            tempPos = []
            for i, val in enumerate(posList):
                self.ser.write(bytes("?CNT" + str(i+1) + "\r\n"), "utf-8")
                tempPos.append(self.ser.readline().decode("utf-8").replace("\r",""))
            if tempPos != posList:
                print(tempPos)
            else:
                print("Position reached...")
                break

        return True


    def motorOff(self):

        # turn x, y, z-motor off
        for i in range(1, 4):
            self.ser.write(bytes("MOFF" + str(i) + "\r\n"), "utf-8")

        print("Motors are off...")

        return True


############################
# absolut movement methods #
############################


    def ref(self):

        # set reference mask for x, y, z
        for i in range(1, 4):
            self.ser.write(bytes("RMK" + str(i) + "=0001\r\n"), "utf-8")


#        # set reference polarity for x, y, z
        # for i in range(1, 4):
        #     if self.model is "PS10":
        #         if self.serList[i-1] is not None:
        #             self.serList[i-1].write(b"RPL1=1111\r\n")
        #         else:
        #             pass
        #     else:
        #         pass
#        for i in range(1, 4):
#            self.ser.write(b"RPL" + str(i) + "=1111\r\n")

        # set reference run velocity for x, y, z (std val = 41943)
        for i in range(1, 4):
            self.ser.write(bytes("RVELS" + str(i) + "=10000\r\n"), "utf-8")


        # set reference mode and start reference run for x, y, z
        for i in range(1, 4):
            self.ser.write(b"REF" + str(i) + "=4\r\n")



        while True:
            self.ser.write(b"?ASTAT\r\n")
            status = self.ser.readline().decode("utf-8").replace("\r","")

            if "P" not in status:
                break
            else:
                pass

        # print final destination
        print("Reference run finished...")
        for i in range(1, 4):
            self.ser.write(bytes("?CNT" + str(i+1) + "\r\n"), "utf-8")
            self.curPos[i] = self.ser.readline().decode("utf-8").replace("\r","")

        print("New position [x, y, z]: " + str(self.curPos).replace("'",""))


        return True


    def moveAbs(self, x, y, z):

        # check if request is within boundaries
        self.checkRange(x, y, z, "Abs")

        newPos = [str(x), str(y), str(z)]

        # send new destination to controller and start motor movement
        for i, val in enumerate(newPos):
            self.ser.write(bytes("PSET" + str(i+1) + "=" + newPos[i] + "\r\n"), "utf-8")
            self.ser.write(bytes("PGO" + str(i+1) + "\r\n"), "utf-8")
        print("Moving to new position...")

        # status request: check and print current position until destination is reached
        self.printPos(newPos)

        # print final destination
        for i, val in enumerate(newPos):
            self.ser.write(bytes("?CNT" + str(i+1) + "\r\n"), "utf-8")
            self.curPos[i] = self.ser.readline().decode("utf-8").replace("\r","")
        print("New position [x, y, z]: " + str(self.curPos).replace("'",""))

        return True



    def moveAbsXY(self, x, y):

        newPosXY = [str(x),str(y)]
        for i in range(1,3):
            self.ser.write(bytes("PSET" + str(i) + "=" + newPosXY[i-1] + "\r\n"), "utf-8")
            self.ser.write(bytes("PGO" + str(i) + "=" + newPosXY[i-1] + "\r\n"), "utf-8")

        while True:
            if self.checkStatus() is True:
                break
            else:
                pass

        # get current position
        for i, val in enumerate(newPos):
            self.ser.write(bytes("?CNT" + str(i+1) + "\r\n"), "utf-8")
            self.curPos[i] = self.ser.readline().decode("utf-8").replace("\r","")

        return True


    def moveAbsZ(self, z):

        self.ser.write(bytes("PSET3=" + str(z) + "\r\n"), "utf-8")
        self.ser.write(b"PGO3\r\n")
        while True:
            if self.checkStatus() is True:
                break
            else:
                pass

        # get current position
        for i, val in enumerate(newPos):
            self.ser.write(bytes("?CNT" + str(i+1) + "\r\n"), "utf-8")
            self.curPos[i] = self.ser.readline().decode("utf-8").replace("\r","")

        return True


    def probe_moveAbs(self, x, y, z=None):

        # z movement is not allowed here for now...
        if z != None:
            OwisError.MotorError("MotorError: Probe station movement is only allowed in the xy-plane for saftey reasons!")
        else:
            pass

        # check if z-drive is possible
        if int(z) < self.zDrive:
            OwisError.MotorError("Probe station movement is not possible without a 1000mu z-drive offset!")
        else:
            pass

        # xy- needs to be seperated from z-movement for most probe station applications
        self.moveAbsZ(z-self.zDrive)
        self.moveAbsXY(x,y)
        self.moveAbsZ(z)
        print("Position reached...")

        # get current position
        for i, val in enumerate(newPos):
            self.ser.write(bytes("?CNT" + str(i+1) + "\r\n"), "utf-8")
            self.curPos[i] = self.ser.readline().decode("utf-8").replace("\r","")

        print("New position [x, y, z]: " + str(self.curPos).replace("'",""))

        return True


#############################
# relative movement methods #
#############################


    def moveRel(self, x, y, z):

        # check if request is within boundaries
        self.checkRange(x, y, z, "Rel")

        newPos = []
        newPos.append(str(int(self.curPos[0]) + int(x)))
        newPos.append(str(int(self.curPos[1]) + int(y)))
        newPos.append(str(int(self.curPos[2]) + int(z)))

        # send new destination to controller and start motor movement
        for i, val in enumerate(newPos):
            self.ser.write(bytes("PSET" + str(i+1) + "=" + newPos[i] + "\r\n"), "utf-8")
            self.ser.write(bytes("PGO" + str(i+1) + "\r\n"), "utf-8")
        print("Moving to new position...")

        # status request: check current position until destination is reached
        self.printPos(newPos)

        # print current destination
        for i, val in enumerate(newPos):
            self.ser.write(bytes("?CNT" + str(i+1) + "\r\n"), "utf-8")
            self.curPos[i] = self.ser.readline().decode("utf-8").replace("\r","")
        print("New position [x, y, z]: " + str(self.curPos).replace("'",""))

        return True


    def moveRelXY(self, x, y):

        newPosXY = []
        newPosXY.append(str(int(self.curPos[0]) + int(x)))
        newPosXY.append(str(int(self.curPos[1]) + int(y)))

        for i in range(1,3):
            self.ser.write(bytes("PSET" + str(i) + "=" + newPosXY[i-1] + "\r\n"), "utf-8")
            self.ser.write(bytes("PGO" + str(i) + "=" + newPosXY[i-1] + "\r\n"), "utf-8")

        while True:
            if self.checkStatus() is True:
                break
            else:
                pass

        # get current position
        for i, val in enumerate(newPos):
            self.ser.write(bytes("?CNT" + str(i+1) + "\r\n"), "utf-8")
            self.curPos[i] = self.ser.readline().decode("utf-8").replace("\r","")

        return True


    def moveRelZ(self, z):

        self.ser.write(bytes("PSET3=" + str(int(self.curPos[2]) + int(z)) + "\r\n"), "utf-8")
        self.ser.write(b"PGO3\r\n")
        while True:
            if self.checkStatus() is True:
                break
            else:
                pass

        # get current position
        for i, val in enumerate(newPos):
            self.ser.write(bytes("?CNT" + str(i+1) + "\r\n"), "utf-8")
            self.curPos[i] = self.ser.readline().decode("utf-8").replace("\r","")

        return True


    def probe_moveRel(self, x, y, z=None):

        Z = int(self.curPos[2])
        # z movement is not allowed here for now...
        if z != None:
            OwisError.MotorError("MotorError: Probe station movement is only allowed in the xy-plane for saftey reasons!")
        else:
            pass

        # check if z-drive is possible
        if (int(self.curPos[2])) < self.zDrive:
            OwisError.MotorError("Probe station movement is not possible without a 1000mu z-drive offset!")
        else:
            pass

        # xy- needs to be seperated from z-movement for most probe station applications
        self.moveAbsZ(Z-self.zDrive)
        self.moveRelXY(x,y)
        self.moveAbsZ(Z)
        print("Position reached...")

        # print current destination
        for i, val in enumerate(newPos):
            self.ser.write(bytes("?CNT" + str(i+1) + "\r\n"), "utf-8")
            self.curPos[i] = self.ser.readline().decode("utf-8").replace("\r","")
        print("New position [x, y, z]: " + str(self.curPos).replace("'",""))

        return True


######################
# conversion methods #
######################


    def ink_to_len(self, posList):

        # convert list elements into integers
        temp = []
        for el in posList:
            temp.append(int(el))
        posList = temp

        # converts [inkrements] into [um]
        posList[0] = str(int(posList[0]/self.xSteps))
        posList[1] = str(int(posList[1]/self.ySteps))
        posList[2] = str(int(posList[2]/self.zSteps))

        return posList


    def len_to_ink(self, posList):

        # convert list elements into integers
        temp = []
        for el in posList:
            temp.append(int(el))
        posList = temp

        # converts [um] to [inkrements]
        posList[0] = str(int(posList[0]*self.xSteps))
        posList[1] = str(int(posList[1]*self.ySteps))
        posList[2] = str(int(posList[2]*self.zSteps))

        return posList


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

            if cmd == "q.":
                break
            else:
                if self.model is "PS35":
                    self.ser.write(cmd + "\r\n")
                    answer = self.ser.readline().decode("utf-8")
                    print(answer)
                elif self.model is "PS10":
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

        o = owis(port1="/dev/ttyACM4", port2="/dev/ttyACM2", port3="/dev/ttyACM5")
        o.init()
        o.checkInit()


        # o.ref()
        # o.test(1)



    except(KeyboardInterrupt):
        print()
        print("Run interrupted.")
        o.motorOff()




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
