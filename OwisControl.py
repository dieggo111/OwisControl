# coding=utf-8
import serial
import time
import sys, os
import OwisError

 

class owis:

    def __init__(self, port=None):
        
        self.logPath = os.getcwd()
        self.logName = "\Logfile.txt"

        self.xRange = 1400000     
        self.yRange = 1400000
        self.zRange = 600000

        self.xSteps = 10000 
        self.ySteps = 10000
        self.zSteps = 50000

        self.zDrive = 50000
        
        if port == None:
            self.port = "COM5"
        else: 
            self.port = port
    
        self.baudrate = 9600
        self.bytesize = 8                    
        self.timeout = 0.12


    def init(self):

        try:    
            self.ser = serial.Serial(   port=self.port, 
                                        baudrate=self.baudrate,                             
                                        bytesize=self.bytesize,
                                        timeout=self.timeout)

            print "Initializing..."

        
        # set denominator of conversion factor for position calculation
        # default val: x = 10000 = 1mm, y = 10000 = 1mm, z = 50000 = 1mm        
#        for i in range(1, 3):        
#            self.ser.write("WMSFAKN" + str(i) + "=10000\r\n")
#        self.ser.write("WMSFAKN3=50000\r\n")
#        # set motor type (3 = Schrittmotor Closed-Loop)
#        self.ser.write("MOTYPE3\r\n")
#        # set current range (Strombereich) for x, y, z (0 = low)        
#        for i in range(1, 4):        
#            self.ser.write("AMPSHNT" + str(i) + "=0\r\n")  
#        # set end switch mask (Endschaltermaske) for x, y, z
#        for i in range(1, 4):        
#            self.ser.write("SMK" + str(i) + "=0110\r\n")     

            # initialize x, y, z-axis with saved default parameters 
            for i in range(1, 4):        
                self.ser.write("INIT" + str(i) + "\r\n")

            # set position format to 'absolute'
            for i in range(1, 4):        
                self.ser.write("ABSOL" + str(i) + "\r\n")

        except:
            raise OwisError.ComError("Comport is already claimed or can not be found!")

    
        return True



########################
# check/status methods #
########################


    def checkInit(self):

        # request current motor position and display values 
        self.curPos = []
        display_counter = []
        for i in range(1, 4):   
            self.ser.write("?CNT" + str(i) + "\r\n")
            self.curPos.append(self.ser.readline().replace("\r",""))       
            self.ser.write("?DISPCNT" + str(i) + "\r\n")                
            display_counter.append(self.ser.readline().replace("\r",""))

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
            print "Current position [x, y, z]: " + str(self.curPos).replace("'","")
        
        return True
    

    def checkStatus(self):

        while True:
            self.ser.write("?ASTAT" + "\r\n")
            status = self.ser.readline().replace("\r","")
                
            if "T" not in status:
                return True
                break
            else:
                pass


    def checkRange(self, x, y, z, mode):

        x = int(x) 
        y = int(y) 
        z = int(z)

        if mode == "Abs":
            if x not in range(0, self.xRange+1) or y not in range(0, self.yRange+1) or z not in range(0, self.zRange+1): 
                raise OwisError.MotorError("Destination is out of motor range!")
            else:
                pass
        
        elif mode == "Rel":    
            if (int(self.curPos[0])+x) not in range(0, self.xRange+1) or (int(self.curPos[1])+y) not in range(0, self.yRange+1) or (int(self.curPos[2])+z) not in range(0, self.zRange+1):
                raise OwisError.MotorError("Destination is out of motor range!")        
            else:
                pass       
        else:
            raise ValueError("Unknown movement mode! Try 'Abs' or 'Rel'.")       
            
        return True   


    def getPos(self):

        return self.ink_to_len(self.curPos, "um")  


#    def getErr(self):
#                
#        self.ser.write("?ERR\r\n")
#        err = self.ser.readline()
#        if err is not "0":
#            print "Unsolved error(s) in memory\n"
#            for el in err:
#                print el + "\n"
#        else:
#            print "No errors to report"
#        cmd = raw_input("Clear memory (y/n)?: ")
#        while cmd not in ("y", "n"):
#            cmd = raw_input("Repeat input: Clear memory (y/n)?: ")
#            if cmd == "y":
#                self.ser.write("ERRCLEAR\r\n") 
#                break
#            elif cmd == "n":
#                break
#                
#        return True
    

    def printPos(self, posList):

        # read-out temp position until requested position is reached
        while True:
            tempPos = []
            for i, val in enumerate(posList):
                self.ser.write("?CNT" + str(i+1) + "\r\n")
                tempPos.append(self.ser.readline().replace("\r",""))
            if tempPos != posList: 
                print tempPos 
            else:
                print "Position reached..."                
                break
                            
        return True    
    

    def motorOff(self):

        # turn x, y, z-motor off
        for i in range(1, 4):        
            self.ser.write("MOFF" + str(i) + "\r\n")           
        print "Motors are off..."

        return True


############################
# absolut movement methods #
############################


    def ref(self):

#        # set reference mask for x, y, z      
#        for i in range(1, 4):        
#            self.ser.write("RMK" + str(i) + "=0001\r\n")
#        # set reference polarity for x, y, z
#        for i in range(1, 4):        
#            self.ser.write("RPL" + str(i) + "=1111\r\n")

        # set reference run velocity for x, y, z (std val = 41943)
        for i in range(1, 4):        
            self.ser.write("RVELS" + str(i) + "=10000\r\n")
       
        # set reference mode and start reference run for x, y, z
        for i in range(1, 4):        
            self.ser.write("REF" + str(i) + "=4\r\n")
    
        while True:
            self.ser.write("?ASTAT" + "\r\n")
            status = self.ser.readline().replace("\r","")
                
            if "P" not in status:
                break
            else:
                pass        

        # print final destination
        print "Reference run finished..." 
        for i, val in enumerate(newPos):        
            self.ser.write("?CNT" + str(i+1) + "\r\n")
            self.curPos[i] = self.ser.readline().replace("\r","")        
        print "New position [x, y, z]: " + str(self.curPos).replace("'","") 

        return True


    def moveAbs(self, x, y, z):

        # check if request is within boundaries       
        self.checkRange(x, y, z, "Abs")
        
        newPos = [str(x), str(y), str(z)]

        # send new destination to controller and start motor movement
        for i, val in enumerate(newPos):        
            self.ser.write("PSET" + str(i+1) + "=" + newPos[i] + "\r\n")                
            self.ser.write("PGO" + str(i+1) + "\r\n")
        print "Moving to new position..."

        # status request: check and print current position until destination is reached
        self.printPos(newPos)

        # print final destination 
        for i, val in enumerate(newPos):        
            self.ser.write("?CNT" + str(i+1) + "\r\n")
            self.curPos[i] = self.ser.readline().replace("\r","")        
        print "New position [x, y, z]: " + str(self.curPos).replace("'","")   

        return True



    def moveAbsXY(self, x, y):

        newPosXY = [str(x),str(y)]
        for i in range(1,3):
            self.ser.write("PSET" + str(i) + "=" + newPosXY[i-1] + "\r\n")                
            self.ser.write("PGO" + str(i) + "=" + newPosXY[i-1] + "\r\n")

        while True:
            if self.checkStatus() is True:
                break
            else:
                pass
        
        # get current position
        for i, val in enumerate(newPos):        
            self.ser.write("?CNT" + str(i+1) + "\r\n")
            self.curPos[i] = self.ser.readline().replace("\r","")  
        
        return True


    def moveAbsZ(self, z):        
        
        self.ser.write("PSET3=" + str(z) + "\r\n")                
        self.ser.write("PGO3\r\n")
        while True:
            if self.checkStatus() is True:
                break
            else:
                pass

        # get current position
        for i, val in enumerate(newPos):        
            self.ser.write("?CNT" + str(i+1) + "\r\n")
            self.curPos[i] = self.ser.readline().replace("\r","")  

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
        print "Position reached..."

        # get current position
        for i, val in enumerate(newPos):        
            self.ser.write("?CNT" + str(i+1) + "\r\n")
            self.curPos[i] = self.ser.readline().replace("\r","") 
        
        print "New position [x, y, z]: " + str(self.curPos).replace("'","")   

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
            self.ser.write("PSET" + str(i+1) + "=" + newPos[i] + "\r\n")                
            self.ser.write("PGO" + str(i+1) + "\r\n")
        print "Moving to new position..."

        # status request: check current position until destination is reached
        self.printPos(newPos)

        # print current destination
        for i, val in enumerate(newPos):        
            self.ser.write("?CNT" + str(i+1) + "\r\n")
            self.curPos[i] = self.ser.readline().replace("\r","")        
        print "New position [x, y, z]: " + str(self.curPos).replace("'","")   

        return True


    def moveRelXY(self, x, y):

        newPosXY = []
        newPosXY.append(str(int(self.curPos[0]) + int(x)))
        newPosXY.append(str(int(self.curPos[1]) + int(y)))
 
        for i in range(1,3):
            self.ser.write("PSET" + str(i) + "=" + newPosXY[i-1] + "\r\n")                
            self.ser.write("PGO" + str(i) + "=" + newPosXY[i-1] + "\r\n")

        while True:
            if self.checkStatus() is True:
                break
            else:
                pass

        # get current position
        for i, val in enumerate(newPos):        
            self.ser.write("?CNT" + str(i+1) + "\r\n")
            self.curPos[i] = self.ser.readline().replace("\r","")   

        return True


    def moveRelZ(self, z):        
        
        self.ser.write("PSET3=" + str(int(self.curPos[2]) + int(z)) + "\r\n")                
        self.ser.write("PGO3\r\n")
        while True:
            if self.checkStatus() is True:
                break
            else:
                pass

        # get current position
        for i, val in enumerate(newPos):        
            self.ser.write("?CNT" + str(i+1) + "\r\n")
            self.curPos[i] = self.ser.readline().replace("\r","")   

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
        print "Position reached..."

        # print current destination
        for i, val in enumerate(newPos):        
            self.ser.write("?CNT" + str(i+1) + "\r\n")
            self.curPos[i] = self.ser.readline().replace("\r","")        
        print "New position [x, y, z]: " + str(self.curPos).replace("'","")  

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
            File.write("{:>0}{:>20}{:>20}".format("x = " + self.curPos[0] , "y = " + self.curPos[1] , "z = " + self.curPos[2])) 
        
        print "Current position saved in Logfile..."

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
#            self.ser.write("DISPCNT" + str(i) + "=" + self.curPos[i-1] + "\r\n") 
#            self.ser.write("CNT" + str(i) + "=" + self.curPos[i-1] + "\r\n") 
#                 
#        print "Recent position coordinates were sent to controler ..."                     
#        print "Current position [x, y, z]: " + str(self.curPos).replace("'","")  
       
        else:
            return True        


################
# test methods #
################

    
    def test_drive(self, Filename):
        
        z = self.curPos[2]
        path = os.getcwd()

        print "Start test drive according to " + Filename[1:]
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
            cmd = raw_input("Enter command:")

            if cmd == "q.":
                break            
            else:
                self.ser.write(cmd + "\r\n")
                answer = self.ser.readline()
                print answer
#                print bin(int(answer))        
        return True      




# main loop
if __name__=='__main__':




    o = owis()
    o.init()    
    o.checkInit()
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


#    print "Run time: " + str(time.time()-start)

## Stresstest mit CPUSTRESS.EXE
## 1%   CPU Auslastung : 91,6 s 
## 75%  CPU Auslastung : 91,7 s
## 100% CPU Auslastung : 91,7 s

