import serial

class owis:

    def __init__(self):
        
        port = "COM5"
        baud = 9600
        bytesize = 8                    
    
        self.ser = serial.Serial(port, baud, bytesize, timeout=0.5)

    
    def init(self):

# Folgende Parameter müssen beim Initialisieren übermittelt werden: Motortyp,
# Endschalter-Maske, Endschalter-Polarität, Achsenparameter/Regelparameter, 
# Strombereich der Motorendstufe. Erst dann kann gefahren werden.

        print "Initializing..."
        
#        self.ser.write("?ERR\r\n")
#        err = self.ser.readline()
#        if err is not "0":
#            print "Unsolved error(s) in memory:\n"
#            for el in err:
#                print el
#        self.ser.write("ERRCLEAR\r\n") 

        
        # Motortyp wählen (3 = Schrittmotor Closed-Loop)
        self.ser.write("MOTYPE3\r\n")
        # Strombereich für Achse 1/2/3 wählen (0 = niedrig)        
        for i in range(1, 3):        
            self.ser.write("AMPSHNT" + str(i) + "=0\r\n")        

    def check(self):

        # check if port is open
        if self.ser.isOpen():
            print(self.ser.name + ' is open...')
        else:
            print "Could not find device :("

    def test(self):

        while True:
            cmd = raw_input("Enter command:")
            if cmd == "q.":
                exit()
            else:
                self.ser.write(cmd+"\r\n")
                answer = self.ser.readline()
                print answer



# main loop
if __name__=='__main__':

    o = owis()
    o.init()
    o.check()
    o.test()


