# coding=utf-8
import serial
import time
import sys, os
import OwisError

 

class owis:

    def __init__(self, model, port1=None, port2=None, port3=None):


        # probe station: PS35
        if model is "PS35":
            self.model = "PS35"
            self.logPath = os.getcwd()
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

        # alibava: PS10
        if model is "PS10":
            self.model = "PS10"
            self.logPath = os.getcwd()
            self.logName = "\Logfile.txt"
            self.serial_nr = ["08070255","08070256","08070257"]
            self.serList = []

            self.xRange = 800000
            self.yRange = 800000
            self.zRange = 635000

            self.xSteps = 10000 
            self.ySteps = 10000
            self.zSteps = 50

            self.zDrive = None

            self.port1 = port1
            self.port2 = port2
            self.port3 = port3

        else:
            raise ValueError("Unkown model")

        # default parameters for serial port
        self.baudrate = 9600
        self.bytesize = 8
        self.timeout = 0.12


    def init(self):

        if self.model is "PS35":
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

        elif self.model is "PS10":
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
                if self.model is "PS10":
                    if self.serList[i-1] is not None:
                        self.serList[i-1].write(b"TERM=0\r\n")
                        self.serList[i-1].readline().decode("utf-8")
                    else:
                        pass
                elif self.model is "PS35":
                    self.ser.write(b"TERM=0\r\n")
                    self.ser.readline().decode("utf-8")
                else:
                    pass

            # set position format to 'absolute'
            for i in range(1, 4):
                if self.model is "PS10":
                    if self.serList[i-1] is not None:
                        self.serList[i-1].write(b"ABSOL1\r\n")
                    else:
                        pass
                elif self.model is "PS35":
                    self.ser.write(bytes("ABSOL" + str(i) + "\r\n"), "utf-8")
                else:
                    pass

            # set position format to 'absolute'
            for i in range(1, 4):
                if self.model is "PS10":
                    if self.serList[i-1] is not None:
                        self.serList[i-1].write(b"EFREE1\r\n")
                    else:
                        pass
                elif self.model is "PS35":
                    self.ser.write(bytes("ABSOL" + str(i) + "\r\n"), "utf-8")
                else:
                    pass

            # set axis order
            self.PS10_idnAxis()

        return True


########################
# check/status methods #
########################


    def checkInit(self):
        
        if self.model is "PS35":
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
                    raise OwisError.SynchError("Unexpected axis positions. Motor needs to be   calibrated!")
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


        elif self.model is "PS10":
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
#                elif val != None and int(val) < 0:
#                    raise OwisError.SynchError("Unexpected axis positions. Motor needs to be   calibrated!")
                else:
                    pass

            print("Current position [x, y, z]: " + str(self.curPos).replace("'",""))

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


    def getPos(self):

        return self.ink_to_len(self.curPos, "um")  


#    def getErr(self):
#                
#        self.ser.write(b"?ERR\r\n")
#        err = self.ser.readline().decode("utf-8")
#        if err is not "0":
#            print("Unsolved error(s) in memory\n")
#            for el in err:
#                print(el + "\n")
#        else:
#            print("No errors to report")
#        cmd = raw_input("Clear memory (y/n)?: ")
#        while cmd not in ("y", "n"):
#            cmd = raw_input("Repeat input: Clear memory (y/n)?: ")
#            if cmd == "y":
#                self.ser.write(b"ERRCLEAR\r\n") 
#                break
#            elif cmd == "n":
#                break
#                
#        return True
    

    def printPos(self, posList):

        # read-out temp position until requested position is reached
        if self.model is "PS35":
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

        elif self.model is "PS10":
            while True:
                tempPos = [None,None,None]
                for i, val in enumerate(posList):
                    for i in range(1, 4):
                        if self.serList[i-1] is not None:
                            self.serList[i-1].write(b"?CNT1\r\n")
                            tempPos[i-1] = self.serList[i-1].readline().decode("utf-8").replace("\r","")
                        else:
                            pass
                if tempPos != posList: 
                    print(tempPos)
                else:
                    print("Position reached...")
                    break

        return True    
    

    def motorOff(self):

        # turn x, y, z-motor off
        for i in range(1, 4):
            if self.model is "PS35":
                self.ser.write(bytes("MOFF" + str(i) + "\r\n"), "utf-8")
            elif self.model is "PS10":
                if self.serList[i-1] is not None:
                    self.serList[i-1].write(b"MOFF1\r\n")
                else:
                    pass
            else:
                pass
            print("Motors are off...")

        return True


############################
# absolut movement methods #
############################


    def ref(self):

#        # set reference mask for x, y, z      
#        for i in range(1, 4):        
#            self.ser.write(b"RMK" + str(i) + "=0001\r\n")
#        # set reference polarity for x, y, z
#        for i in range(1, 4):        
#            self.ser.write(b"RPL" + str(i) + "=1111\r\n")

        # set reference run velocity for x, y, z (std val = 41943)
        for i in range(1, 4):
            if self.model is "PS10":
                if self.serList[i-1] is not None:
                    self.serList[i-1].write(b"RVELS1=1000\r\n")
                else:
                    pass
            elif self.model is "PS35":
                self.ser.write(bytes("RVELS" + str(i) + "=10000\r\n"), "utf-8")
            else:
                pass

        # set reference mode and start reference run for x, y, z
        for i in range(1, 4):        
            if self.model is "PS10":
                if self.serList[i-1] is not None:
                    self.serList[i-1].write(b"REF1=4\r\n")
                else:
                    pass
            elif self.model is "PS35":
                self.ser.write(b"REF" + str(i) + "=4\r\n")
            else:
                pass


        if self.model is "PS35":
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


        if self.model is "PS10":
            ref = True
            while ref is True:
                for i in range(1, 4):
                    ref = True
                    if self.serList[i-1] is not None:
                        self.serList[i-1].write(b"?ASTAT\r\n")
                        status = self.serList[i-1].readline().decode("utf-8").replace("\r","")
                    else:
                        pass
                    if "P" not in status:
                        ref = False
                    else:
                        pass

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


    def ink_to_len(self, posList, unit):

        temp = []
        for el in posList:
            temp.append(int(el))
        posList = temp
    
        # converts [inkrements] into [um]/[mm] 
        if unit is "mm":
            posList[0] /= self.xSteps       
            posList[1] /= self.ySteps
            posList[2] /= self.zSteps
        elif unit is "um":
            posList[0] /= (self.xSteps/1000)       
            posList[1] /= (self.ySteps/1000)
            posList[2] /= (self.zSteps/1000)
        else:
            raise ValueError("Unknown unit")            

        temp = []
        for el in posList:
            temp.append(str(el))
        posList = temp

        return posList


    def len_to_ink(self, posList, unit):

        temp = []
        for el in posList:
            temp.append(int(el))
        posList = temp
    
        # converts [um]/[mm] to [inkrements] 
        if unit is "mm":
            posList[0] *= self.xSteps       
            posList[1] *= self.ySteps
            posList[2] *= self.zSteps
        elif unit is "um":
            posList[0] *= (self.xSteps/1000)       
            posList[1] *= (self.ySteps/1000)
            posList[2] *= (self.zSteps/1000)
        else:
            raise ValueError("Unknown unit")            

        temp = []
        for el in posList:
            temp.append(str(el))
        posList = temp

        return posList


###############
# log methods #
###############


    def writeLog(self):

        with open(self.logPath + self.logName, "w") as File:
            File.write(b"{:>0}{:>20}{:>20}".format("x = " + self.curPos[0] , "y = " + self.curPos[1] , "z = " + self.curPos[2])) 
        
        print("Current position saved in Logfile...")

        return True


    def readLog(self):

        logPos = []

        with open(self.logPath + self.logName, "r") as File:
            line = File.readline().decode("utf-8").split() 
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


#################
# PS 10 methods #
#################


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


    def PS10_moveRel(self, x, y, z):

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
    

    def test(self):

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
                    self.serList[2].write(bytes(cmd + "\r\n", "utf-8"))
                    answer = self.serList[2].readline().decode("utf-8")
                    print(answer)
        return True






# main loop
if __name__=='__main__':




    o = owis("PS10", port1="/dev/ttyACM0", port2="/dev/ttyACM1", port3="/dev/ttyACM2")
    o.init()
    o.checkInit()

#    o.PS10_moveRel(100000,200000,60000)
#    o.ref()
#    o.PS10_moveRel(0,0,1000)
#    o.moveRel(50000,0,0)

#    o.readLog()
#    o.test()

#    o.check_zDrive()
#    o.probe_moveAbs(1000,50000,50000)

#    o.moveAbsXY(55000,55000)
#    o.ref()
##    o.moveAbsZ()

    o.motorOff()

#    o.moveAbs(1000000, 1000000, 400000)
#    o.moveAbs(10000, 10000, 100000)

##    o.check_zDrive()
##    o.test_drive("\Speedtest.txt")

#    o.writeLog()


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


