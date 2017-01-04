# coding=utf-8
import serial
import time
import sys, os 

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
            port = "COM4"
        else: 
            pass
    
        baud = 9600
        bytesize = 8                    
            
        self.ser = serial.Serial(port, baud, bytesize, timeout=0.12)



    def init(self):

        print "Initializing..."

        self.checkCOM()
        
        # initialize x, y, z-axis with saved default parameters 
        for i in range(1, 4):        
            self.ser.write("INIT" + str(i) + "\r\n")

        # set denominator of conversion factor for position calculation
        # default val: x = 10000 = 1mm, y = 10000 = 1mm, z = 50000 = 1mm        
#        for i in range(1, 3):        
#            self.ser.write("WMSFAKN" + str(i) + "=10000\r\n")
#        self.ser.write("WMSFAKN3=50000\r\n")

        # set position format to 'absolute'
        for i in range(1, 4):        
            self.ser.write("ABSOL" + str(i) + "\r\n")
        
        # request current position or load recent position from logfile
        self.curPos = []
        display_counter = []
#        if self.readLog(os.getcwd()) is False:
        if True:
            for i in range(1, 4):        
                self.ser.write("?CNT" + str(i) + "\r\n")
                self.curPos.append(self.ser.readline().replace("\r",""))  
                self.ser.write("?DISPCNT" + str(i) + "\r\n")                
                display_counter.append(self.ser.readline().replace("\r",""))

            if display_counter != self.curPos:
                raise ValueError("Synchronization Error: Display counter and motor position are unequal.")
            print "Current position [x, y, z]: " + str(self.curPos).replace("'","")
        
        for val in self.curPos:
            if val == "":
                raise ValueError("Communication error: Could not get proper position information in time.")
            elif val != None and int(val) < 0:
                raise ValueError("Synchronization Error: Unexpected axis positions. Motor needs to be calibrated.")
            else:
                pass                 

        return self.ink_to_len(self.curPos, "um")


        
#        # set motor type (3 = Schrittmotor Closed-Loop)
#        self.ser.write("MOTYPE3\r\n")
#        # set current range (Strombereich) for x, y, z (0 = low)        
#        for i in range(1, 4):        
#            self.ser.write("AMPSHNT" + str(i) + "=0\r\n")  
#        # set end switch mask (Endschaltermaske) for x, y, z
#        for i in range(1, 4):        
#            self.ser.write("SMK" + str(i) + "=0110\r\n")        
             
       
    def getPos(self):

        return self.curPos             


    
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
        
        self.checkStatus()
        self.curPos = ["0","0","0"] 
        print "Reference run finished..."


        return True


    def checkCOM(self):

        # check if port is open
        if self.ser.isOpen():
            print(self.ser.name + ' is open...')
        else:
            raise ValueError("Communication Error: Could not find device :(") 

        return True


    def getErr(self):
                
        self.ser.write("?ERR\r\n")
        err = self.ser.readline()
        if err is not "0":
            print "Unsolved error(s) in memory\n"
            for el in err:
                print el + "\n"
        else:
            print "No errors to report"
        cmd = raw_input("Clear memory (y/n)?: ")
        while cmd not in ("y", "n"):
            cmd = raw_input("Repeat input: Clear memory (y/n)?: ")
            if cmd == "y":
                self.ser.write("ERRCLEAR\r\n") 
                break
            elif cmd == "n":
                break
                
        return True


    def moveAbs(self, x, y, z):

        # check if request is within boundaries       
        self.checkRange(x, y, z)
        
        newPos = [str(x), str(y), str(z)]

        # send new destination to controller and start motor movement
        for i, val in enumerate(newPos):        
            self.ser.write("PSET" + str(i+1) + "=" + newPos[i] + "\r\n")                
            self.ser.write("PGO" + str(i+1) + "\r\n")
        print "Moving to new position..."

        # status request: check current position until destination is reached
        self.printPos(newPos)

        # print current destination
        for i, val in enumerate(newPos):        
            self.ser.write("?PSET" + str(i+1) + "\r\n")
            self.curPos[i] = self.ser.readline().replace("\r","")        
        print "New position [x, y, z]: " + str(self.curPos).replace("'","")   

        return self.curPos


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
    

    def checkStatus(self):

        while True:
            self.ser.write("?ASTAT" + "\r\n")
            status = self.ser.readline().replace("\r","")
            if "T" not in status:
                return True
                break
            else:
                pass


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

        return True


    def moveAbsZ(self, z):        
        
        self.ser.write("PSET3=" + str(z) + "\r\n")                
        self.ser.write("PGO3\r\n")
        while True:
            if self.checkStatus() is True:
                break
            else:
                pass

        return True


    def probe_moveAbs(self, x, y, z):
        
        # xy- needs to be seperated from z-movement for most probe station applications   
        self.moveAbsZ(z-self.zDrive)
        self.moveAbsXY(x,y)       
        self.moveAbsZ(z)
        self.curPos[str(x),str(y),str(z)]
        print "Position reached..."

        return self.curPos


    def check_zDrive(self):

        # get current z-position and make sure z-drive = 1mm = 50000 is possible
        self.ser.write("?CNT3\r\n")
        z = int(self.ser.readline().replace("\r",""))
        if z < self.zDrive:
            raise ValueError("Motor Error: Probe station movement is not possible without a 1000mu z-drive offset!")
        else:
            pass

        return True



    def motorOff(self):

        # turn x, y, z-motor off
        for i in range(1, 4):        
            self.ser.write("MOFF" + str(i) + "\r\n")           
        print "Motors are off..."

        return True


    def checkRange(self, x, y, z):

        x = int(x) 
        y = int(y) 
        z = int(z)

        if x not in range(0, self.xRange+1) or y not in range(0, self.yRange+1) or z not in range(0, self.zRange+1): 
            raise ValueError("Motor Error: Destination is out of motor range!") 
        else:
            pass

        return True     




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















## main loop
#if __name__=='__main__':




#    o = owis()
#    o.init()
#    

#    o.readLog()
#    o.test()

##    o.check_zDrive()
##    o.probe_moveAbs(800000,800000,400000)

##    o.moveAbsXY(50000,50000)
##    o.ref()
##    o.moveAbsZ()

##    o.motorOff()

##    o.writeLog(os.getcwd())

##    o.moveAbs(1000000, 1000000, 400000)
##    o.moveAbs(750000, 750000, 400000)

##    o.check_zDrive()
##    o.test_drive("\Speedtest.txt")

#    print "Run time: " + str(time.time()-start)

## Stresstest mit CPUSTRESS.EXE
## 1%   CPU Auslastung : 91,6 s 
## 75%  CPU Auslastung : 91,7 s
## 100% CPU Auslastung : 91,7 s

