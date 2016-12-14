# coding=utf-8
import serial

class owis:

    def __init__(self):
        
        port = "COM5"
        baud = 9600
        bytesize = 8                    
    
        self.ser = serial.Serial(port, baud, bytesize, timeout=0.5)

    
    def init(self):

    # Folgende Parameter muessen beim Initialisieren uebermittelt werden: Motortyp,
    # Endschalter-Maske, Endschalter-Polaritaet, Achsenparameter/Regelparameter, 
    # Strombereich der Motorendstufe. Erst dann kann gefahren werden.

        print "Initializing..."
        
#        # Motortyp waehlen (3 = Schrittmotor Closed-Loop)
#        self.ser.write("MOTYPE3\r\n")
#        # Strombereich für Achse 1/2/3 waehlen (0 = niedrig)        
#        for i in range(1, 4):        
#            self.ser.write("AMPSHNT" + str(i) + "=0\r\n")  
        

        # Achse 1/2/3 initialisieren mit gespeicherten Standardparametern        
        for i in range(1, 4):        
            self.ser.write("INIT" + str(i) + "\r\n")
        for i in range(1, 4):        
            print "INIT" + str(i) + "\r\n"
                    
    
    def ref(self):

        # Referenzmaske fuer Achse 1/2/3 waehlen      
        for i in range(1, 4):        
            self.ser.write("RMK" + str(i) + "=0001\r\n")
        # Referenzschalterpolaritaet fuer Achse !/2/3 waehlen
        for i in range(1, 4):        
            self.ser.write("RPL" + str(i) + "=0001\r\n")
         
        return True

        
  

    def check(self):

        # check if port is open
        if self.ser.isOpen():
            print(self.ser.name + ' is open...')
        else:
            print "Could not find device :("

        return True


    def test(self):

        while True:
            cmd = raw_input("Enter command:")
            if cmd == "q.":
                exit()
            else:
                self.ser.write(cmd+"\r\n")
                answer = self.ser.readline()
                print answer

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

# main loop
if __name__=='__main__':

    o = owis()
    o.init()
    o.check()
    o.test()


