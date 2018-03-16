# coding=utf-8
import serial, time, os
import OwisError

class owis:

    def __init__(self, port=None):


        self.logPath = os.getcwd()
        self.logName = "Logfile.txt"
        self.axis_timeout = 120
        self.ref_timeout = 40
        self.curPos = []

        # for Owis motor stages from 2016
        # x_max is about 195 mm =  1400000 ink
        self.xRange = 1950000
        # y_max is about 195 mm =  1400000 ink
        self.yRange = 1950000
        # x_max is about 30 mm =  600000 ink
        self.zRange = 600000

        # ink steps per um
        self.xSteps = 10
        self.ySteps = 10
        self.zSteps = 20

        self.zDrive = 20000

        if port == None:
            self.port = "COM4"
        else:
            self.port = port

        # default parameters for serial port
        self.baudrate = 9600
        self.bytesize = 8
        self.timeout = 0.15


        try:
            self.ser = serial.Serial(port=self.port,
                                     baudrate=self.baudrate,
                                     bytesize=self.bytesize,
                                     timeout=self.timeout)

            print("Established motor connection successfully...")

            # initialize x, y, z-axis with saved default parameters
            self.checkStatus()
            for i in range(1, 4):
                self.ser.write(bytes("INIT" + str(i) + "\r\n", "utf-8"))
        except:
            raise OwisError.ComError("Comport is already claimed or can not be found!")

        self.checkStatus()



    def init(self):


        # set terminal mode to '0' (short answer)
        # controller that was set to 'TERM=2' will send one last 'OK'
        for i in range(1, 4):
            self.ser.write(b"TERM=0\r\n")
            self.ser.readline().decode("utf-8")

        # set position format to 'absolute'
        for i in range(1, 4):
            self.ser.write(bytes("ABSOL" + str(i) + "\r\n", "utf-8"))

        # set display mode to 'mm'
        for i in range(1, 4):
            self.ser.write(bytes("PWMSMODE" + str(i) + "=1\r\n", "utf-8"))

        print("Initializing...")

        return True


########################
# check/status methods #
########################


    def checkInit(self):

        # request current motor position and display values
        display_counter = []
        for i in range(1, 4):
            self.ser.write(bytes("?CNT" + str(i) + "\r\n", "utf-8"))
            self.curPos.append(self.ser.readline().decode("utf-8").replace("\r",""))
            self.ser.write(bytes("?DISPCNT" + str(i) + "\r\n", "utf-8"))
            display_counter.append(self.ser.readline().decode("utf-8").replace("\r",""))

        for val in self.curPos:
            # check if serial-timeout is sufficient
            if val == "":
                raise OwisError.ComError("Could not get proper position information in time!")
            # check if current position is in the expected range
            elif val != None and int(val) < 0:
                print("Warning: Unexpected axis positions. Motor needs to be calibrated!")
                # raise OwisError.SynchError("Unexpected axis positions. Motor needs to be calibrated!")
            else:
                pass

        # check if display counter and motor position are equal
        if display_counter != self.curPos:
            # raise OwisError.SynchError("Display counter and motor position are unequal!")
            print("Warning: Display counter and motor position are unequal.")

        print("Current position in (um) [x, y, z]: [" \
              + self.getPos("str") + "]")

        return True


    def checkLog(self):

        # create logfile if it isn't there
        if os.path.isfile(os.path.join(self.logPath,self.logName)) is False:
            self.writeLog()
            print("Created new Logfile...")
        # check if motor position and log position are equal
        elif self.readLog() is False:
            print("Warning: Display counter and motor position are unequal.")
        else:
            return True


    def checkStatus(self, mode=None, timeout=None):
        """ Checks axis status and returns 'true' when movement is finished
        ('RRR').
        args:
        'mode'      : prints status tripplet if 'print'
        'timeout'   : terminates the loop if time has run out (time in sec,
                      default is no timeout)

        """
        if timeout != None:
            end_time = time.time() + timeout
        else:
            end_time = None
        while True:
            self.ser.write(b"?ASTAT\r\n")
            status = self.ser.readline().decode("utf-8").replace("\r","")
            if mode == "print":
                self.printAll(status)
            if status == "RRR":
                return True
                break
            elif end_time != None and time.time() > end_time:
                return "timeout"
            else:
                return False

    def checkRange(self, x, y, z):
        """ Checks if new position is within the accepted range according to
        the 'self.(x,y,z)Range' values. Only absolute values can be checked.
        Method expects arguments to be in [ink].

        """

        checkList = [int(x),int(y),int(z)]

        rangeList = [self.xRange,self.yRange,self.zRange]

#        if (checkList[0] not in range(0, self.xRange+1))\
#        or (checkList[1] not in range(0, self.yRange+1))\
#        or (checkList[2] not in range(0, self.zRange+1)):
#            raise OwisError.MotorError("Destination is out of motor range!")
#        else:
#            pass

        if (checkList[0] not in range(0, self.xRange+1))\
        or (checkList[1] not in range(0, self.yRange+1)):
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



    def getStatus(self):
        """ Returns current axis status.

        """

        self.ser.write(b"?ASTAT\r\n")
        temp = self.ser.readline().decode("utf-8").replace("\r","")

        status = temp[0] + "," + temp[1] + "," + temp[2]

        return status


    def printAll(self, status):
        """ Prints current axis status and current position.

        """

        tempPos = [None,None,None]

        for i in range(1, 4):
            self.ser.write(bytes("?CNT" + str(i) + "\r\n", "utf-8"))
            tempPos[i-1] = self.ser.readline().decode("utf-8").replace("\r","")

        print("status = " + "[" + self.getStatus() + "]" + " ; position = " + str(self.ink_to_len(tempPos)))

        return True


    def freeMotor(self):

        status = [None,None,None]

        for i in range(1, 4):
            if self.ser is not None:
                self.ser.write(b"?ASTAT\r\n")
                status[i-1] = self.ser.readline().decode("utf-8").replace("\r","")
            else:
                pass

        for i in range(1, 4):
            self.ser.write(bytes("INIT"+ str(i) + "\r\n", "utf-8"))
            time.sleep(2)
            self.ser.write(bytes("EFREE"+ str(i) + "\r\n", "utf-8"))

        return True


#######################
# PS 35 motor methods #
#######################


    def MOVA(self, x, y, z):
        """ Sends new position to controller and starts the movement. Position
        is written into logfile if run is succesfull.
        (x,y,z) arguments are considered as [um]. It is important to note
        that the controller expects [inkrement] values!

        Args:
        x,y,z : int or str (value in [um])
        ...
        self.curPos : [str,str,str]

        """

        # convert [um] values into [ink]
        newPos = self.len_to_ink([x,y,z])

        # check if request is within boundaries
        self.checkRange(newPos[0],newPos[1],newPos[2])

        # send new destination to controller and start motor movement
        for i in enumerate(newPos):
            self.ser.write(bytes("PSET" + str(i+1) + "=" + newPos[i] + "\r\n", "utf-8"))
            self.ser.write(bytes("PGO" + str(i+1) + "\r\n", "utf-8"))

        print("Moving to new position...")

        # status request: check current position and status until destination is reached
        while True:
            if self.checkStatus() == True:
                break
            elif self.checkStatus(timeout=self.axis_timeout) == "timeout":
                self.motorOff()
                raise ValueError("Warning: Movement error. Couldn't reach " +
                                 "expected position in time.")
            else:
                pass

        # read-out final position
        for i in enumerate(newPos):
            self.ser.write(bytes("?CNT" + str(i+1) + "\r\n", "utf-8"))
            self.curPos[i] = self.ser.readline().decode("utf-8").replace("\r","")

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
            # 1 = 0001 = MINSTOP
            # 2 = 0010 = MINDEC
            # 4 = 0100 = MAXDEC
            self.ser.write(bytes("RMK" + str(i) + "=2\r\n", "utf-8"))

        # set reference run velocity for x, y, z (std val = 41943)
        for i in range(1, 4):
            self.ser.write(bytes("RVELS" + str(i) + "=10000\r\n", "utf-8"))

        # set reference mode and start reference run for x, y, z
        if mode is not None:
            for i in range(1, 4):
                self.ser.write(bytes("REF" + str(i) + "=" + str(mode) + "\r\n", "utf-8"))
        else:
            for i in range(1, 4):
                if i == 3:
                    self.ser.write(bytes("REF" + str(i) + "=6\r\n", "utf-8"))
                else:
                    self.ser.write(bytes("REF" + str(i) + "=4\r\n", "utf-8"))


        # status request: check current position and status until destination is reached
        # BUG: there's a bug with z-axis on PS1 that forces me to intercept a stuck axis"
        while True:
            if self.checkStatus(mode="print",timeout=self.ref_timeout) == True:
                break
            elif self.checkStatus(mode="print",timeout=self.ref_timeout) == "timeout":
                print("Warning: Axis got stuck.")
                self.motorOff()
                self.init()
                break
            else:
                pass

        print("Reference run finished...")

        # BUG: z axis counter are resetting automatically on PS1, so I gotta do it manually
        for i in range(1, 4):
            self.ser.write(bytes("CNT" + str(i) + "=0" + "\r\n", "utf-8"))
            self.ser.write(bytes("DISPCNT" + str(i) + "=0" + "\r\n", "utf-8"))

        # read-out final position
        for i in range(1, 4):
            self.ser.write(bytes("?CNT" + str(i) + "\r\n", "utf-8"))
            self.curPos[i-1] = self.ser.readline().decode("utf-8").replace("\r","")

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
            self.ser.write(bytes("MOFF" + str(i) + "\r\n", "utf-8"))

        print("Motors are off...")

        return True


    def MOVA_XY(self, x, y):

        newPosXY = [str(x),str(y)]

        for i in range(1,3):
            self.ser.write(bytes("PSET" + str(i) + "=" + newPosXY[i-1] + "\r\n", "utf-8"))
            self.ser.write(bytes("PGO" + str(i) + "=" + newPosXY[i-1] + "\r\n", "utf-8"))

        while True:
            if self.checkStatus() is True:
                break
            else:
                pass

        return True


    def MOVA_Z(self, z):

        self.ser.write(bytes("PSET3=" + str(z) + "\r\n", "utf-8"))
        self.ser.write(b"PGO3\r\n")

        while True:
            if self.checkStatus() is True:
                break
            else:
                pass

        return True


    def MOPA(self, x, y, z):
        """ Probe station movement that adds a z-drive function to the ordinary
        'MOVA' method.

        Args:
        x,y,z : int or str (value in [um])

        """

        # convert [um] values into [ink]
        newPos = self.len_to_ink([x,y,z])

        # check if z-drive is possible
#        if int(z) < self.zDrive:
#            OwisError.MotorError("Probe station movement is not possible without a 1000mu z-drive offset!")
            # raise ValueError("Probe station movement is not possible without a 1000mu z-drive offset!")
#        else:
#            pass

        # check if request is within boundaries
        # self.checkRange(newPos[0],newPos[1],newPos[2])

        # xy- needs to be seperated from z-movement for most probe station applications
        self.MOVA_Z(int(newPos[2])-self.zDrive)
        self.MOVA_XY(int(newPos[0]),int(newPos[1]))
        self.MOVA_Z(int(newPos[2]))
        print("Position reached...")

        # get current position
        for i in range(0,3):
            self.ser.write(bytes("?CNT" + str(i+1) + "\r\n", "utf-8"))
            self.curPos[i] = self.ser.readline().decode("utf-8").replace("\r","")

        print("New position [x, y, z]: " + str(self.ink_to_len(self.curPos)).replace("'",""))

        return True



    def MOPR(self, x, y, z):

#        if z != None:
#            raise ValueError("z movement in MOPR")
#        else:
#            pass

        # convert [um] values into [ink]
        newRel = self.len_to_ink([x,y,z])

        # TODO: as long as z-stage bug is present
        # if int(self.curPos[2])-self.zDrive-int(newRel[2]) < (-200000):
            # raise OwisError.MotorError("Destination is out of motor range!")

        # pure z-movements don't need zDrive
        if (x,y) == ("0","0"):
            self.MOVA_Z(int(self.curPos[2])+int(newRel[2]))
        # xy-movements require zDrive for safety reasons
        else:
            self.MOVA_Z(int(self.curPos[2])-self.zDrive+int(newRel[2]))
            # xy- needs to be seperated from z-movement for most probe station applications
            self.MOVA_XY(int(self.curPos[0])+int(newRel[0]),int(self.curPos[1])+int(newRel[1]))
            self.MOVA_Z(int(self.curPos[2])+int(newRel[2]))
        print("Position reached...")

        # print current destination
        for i in range(0,3):
            self.ser.write(bytes("?CNT" + str(i+1) + "\r\n", "utf-8"))
            self.curPos[i] = self.ser.readline().decode("utf-8").replace("\r","")
        print("New position [x, y, z]: " + str(self.ink_to_len(self.curPos)).replace("'",""))

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

        with open(os.path.join(self.logPath,self.logName), "w") as File:
            File.write("{:>0}{:>20}{:>20}".format("x = " + temp[0] , "y = " + temp[1] , "z = " + temp[2]))

        print("Current position saved in Logfile...")

        return True


    def readLog(self):
        """ Reads log position and compares it with cuurent position.

        """

        logPos = []

        with open(os.path.join(self.logPath,self.logName), "r") as File:
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


    def test_drive(self, Filename):

        z = self.curPos[2]
        path = os.getcwd()

        print("Start test drive according to " + Filename[1:])
        with open(path + Filename, "r") as File:
            for line in File:
                try:
                    (x,y) = line.split()
                    self.MOVA(int(x)*self.xSteps,int(y)*self.xSteps,z)
                except:
                    pass

        return True


    def test(self):

        print("###############################################################")
        print("Test function started. Ready to send commands to controllers")
        print("Table of commands: http://www.owis.eu/fileadmin/_migrated/content_uploads/PS_10_Betriebsanleitung_2014.pdf")
        print("Type 'q' to exit and turn off motor.")

        while True:
            cmd = input("Enter command:")

            if cmd == "q":
                print("Test programm closed.")
                self.motorOff()
                break
            else:
                self.ser.write(bytes(cmd + "\r\n", "utf-8"))
                answer = self.ser.readline().decode("utf-8")
                print(answer)

        return True





# main loop
if __name__=='__main__':


    try:
        o = owis(port = "COM5")
        o.init()
        o.checkInit()
        o.test()
        # o.MOPR(0,0,-1000)
#        o.MOPA(60000,60000,-130000)
#         o.REFDRIVE()
#        o.motorOff()
    except(KeyboardInterrupt):
        print()
        print("Run interrupted.")


    finally:
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
