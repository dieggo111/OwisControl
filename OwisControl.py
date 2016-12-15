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

        # set reference mode (Referenzfahrtmodus) and start reference run for x, y, z
        for i in range(1, 4):        
            self.ser.write("REF" + str(i) + "=4\r\n")
        
        self.checkPos(["0","0","0"],0.2)
        print "Reference run finished..."

        # status request for x, y, z         
        self.ser.write("?ASTAT\r\n") 
        print self.ser.readline()
        
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
       
        if 0 > x > 1400000 or 0 > y > 1400000 or 0 > z > 100000:
            print "Out of range!"
            exit()
        
        newPos = [str(x), str(y), str(z)]

        # send new position to controller and start motor movement
        for i, val in enumerate(newPos):        
            self.ser.write("PSET" + str(i+1) + "=" + newPos[i] + "\r\n")                
            self.ser.write("PGO" + str(i+1) + "\r\n")
        print "Moving to new position..."

        # status request: check current position until goal is reached
        self.checkPos(newPos, 0.2)
        
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

    def Zdrive(self, z):
        
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
#    o.moveAbs(100000, 100000, 0)
#    o.ref()


