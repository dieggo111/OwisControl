# coding=utf-8
import serial
import time
import sys 

class owis:

    def __init__(self):
        
        port = "COM5"
        baud = 9600
        bytesize = 8                    
            
        self.ser = serial.Serial(port, baud, bytesize, timeout=0.1)

        # timeout needs to be >= 0.1 for the controller to be able to answer a call     


    def init(self):


        print "Initializing..."

        self.checkCOM()
        
        # initialize x, y, z-axis with saved default parameters 
        for i in range(1, 4):        
            self.ser.write("INIT" + str(i) + "\r\n")

        # request current position
        self.curPos = []
        for i in range(1, 4):        
            self.ser.write("?CNT" + str(i) + "\r\n")
            self.curPos.append(self.ser.readline().replace("\r",""))  
      
        print "Current position [x, y, z]: " + str(self.curPos).replace("'","")
        
        for val in self.curPos:
            if int(val) < 0:
                sys.exit("Unexpected axis positions. Motor needs to be calibrated.")
            else:
                pass                 




    # Folgende Parameter muessen beim Initialisieren uebermittelt werden: Motortyp,
    # Endschalter-Maske, Endschalter-Polaritaet, Achsenparameter/Regelparameter, 
    # Strombereich der Motorendstufe. Erst dann kann gefahren werden.

        
#        # set motor type (3 = Schrittmotor Closed-Loop)
#        self.ser.write("MOTYPE3\r\n")
#        # set current range (Strombereich) for x, y, z (0 = low)        
#        for i in range(1, 4):        
#            self.ser.write("AMPSHNT" + str(i) + "=0\r\n")  
#        # set end switch mask (Endschaltermaske) for x, y, z
#        for i in range(1, 4):        
#            self.ser.write("SMK" + str(i) + "=0110\r\n")        
             
       
    
    def ref(self):

#        # set reference mask (Referenzmaske) for x, y, z      
#        for i in range(1, 4):        
#            self.ser.write("RMK" + str(i) + "=0001\r\n")

#        # set reference polarity (Referenzpolaritaet) for x, y, z
#        for i in range(1, 4):        
#            self.ser.write("RPL" + str(i) + "=1111\r\n")

#        # set reference run velocity for x, y, z (std val = 41943)
#        for i in range(1, 4):        
#            self.ser.write("RVELS" + str(i) + "=2000\r\n")
       
        # set reference mode (Referenzfahrtmodus) and start reference run for x, y, z
        for i in range(1, 4):        
            self.ser.write("REF" + str(i) + "=4\r\n")
        
        self.checkPos(["0","0","0"],0.2)
        print "Reference run finished..."

        # status request for x, y, z         
        self.ser.write("?ASTAT\r\n") 
        print "Current status of x, y, z-axis: " + self.ser.readline()
        
        return True

        

    def checkCOM(self):

        # check if port is open
        if self.ser.isOpen():
            print(self.ser.name + ' is open...')
        else:
        # raises error "could not open port"
            sys.exit("Could not find device :(") 
         

        return True


    def getErr(self):
                
        self.ser.write("?ERR\r\n")
        err = self.ser.readline()
        if err is not "0":
            print "Unsolved error(s) in memory\n"
            for el in err:
                print el + "\n"
        else:
            print "No errors to report\n"
        cmd = raw_input("Clear memory (y/n)?:\n")
        while (cmd is not "y") or (cmd is not "n"):
            cmd = raw_input("Repeat input: Clear memory (y/n)?:\n")
            if cmd == "y":
                self.ser.write("ERRCLEAR\r\n") 
            elif cmd == "n":
                pass

        return True


    def moveAbs(self, x, y, z):

        # check if request is within boundaries       
        if 0 > x > 1400000 or 0 > y > 1400000 or 0 > z > 100000:
            sys.exit("Out of range!") 
        
        newPos = [str(x), str(y), str(z)]

        # send new destination to controller and start motor movement
        for i, val in enumerate(newPos):        
            self.ser.write("PSET" + str(i+1) + "=" + newPos[i] + "\r\n")                
            self.ser.write("PGO" + str(i+1) + "\r\n")
        print "Moving to new position..."

        # status request: check current position until destination is reached
        self.checkPos(newPos, 0.2)
        
        # print current destination
        for i, val in enumerate(newPos):        
            self.ser.write("?PSET" + str(i+1) + "\r\n")
            self.curPos[i] = self.ser.readline().replace("\r","")        
        print "New position [x, y, z]: " + str(self.curPos).replace("'","")   

        return True


    def checkPos(self, pos, wait):

        # read-out temp position until requested position is reached
        while True:
            tempPos = []
            for i, val in enumerate(pos):
                self.ser.write("?CNT" + str(i+1) + "\r\n")
                tempPos.append(self.ser.readline().replace("\r",""))
            if tempPos != pos: 
                print tempPos 
                time.sleep(wait)           
            else:
                print "Position reached..."                
                break

        return True        
                        
    
        return True    
    
    def moveAbsXY(self, x, y, Z = None):

        # get current z-position
        if Z == None:
            self.ser.write("?CNT3\r\n")
            Z = self.ser.readline().replace("\r","")
        else:
            self.moveAbs(x, y, Z)

        return True


    def moveAbsZ(self, z):        
        
        # get current xy-position
        self.ser.write("?CNT1\r\n")
        X = self.ser.readline().replace("\r","")
        self.ser.write("?CNT2\r\n")
        Y = self.ser.readline().replace("\r","")

        self.moveAbs(X, Y, z)

        return True


    def probe_moveAbs(self, x, y):
        
        # xy- needs to be seperated from z-movement for most probe station applications   

        # get current z-position and make sure z-drive is possible
        self.ser.write("?CNT3\r\n")
        z = self.ser.readline().replace("\r","")
        if int(z) < 1000:
            sys.exit("Probe station movement is not possible without a 1000mu z-drive offset!")
        else:
            self.moveAbsZ(z-1000)

        self.moveAbsXY(x, y, z-1000)


        return True


    def test(self):

        while True:
            cmd = raw_input("Enter command:")
            if cmd == "q.":
                exit()            
            else:
                self.ser.write(cmd + "\r\n")
                answer = self.ser.readline()
                #print (answer, bin(int(answer)))
                print answer

        return True     

    def motorOff(self):

        # turn x, y, z-motor off
        for i in range(1, 4):        
            self.ser.write("MOFF" + str(i) + "\r\n")           
        print "Motors are off..."




# main loop
if __name__=='__main__':


    o = owis()
    o.init()
    o.test()
#    o.moveAbs(100001, 100001, 500001)
#    o.ref()
#    o.moveAbsZ()


###########################################
# x,y : 100000 = 10mm | z : 500000 = 10mm #
###########################################

