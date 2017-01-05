import socket
import sys, os
import OwisControl


init = False



# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the port
server_address = ('localhost', 10000)
print 'starting up on %s port %s' % server_address

# Bind socket sock with the server adress local host with port 10000
sock.bind(server_address) 

# Listen for incoming connections
sock.listen(1)

while True:
    # Wait for a connection / press Ctrl+Break(Pause) to abort
    print 'wait for a connection'
    connection, client_address = sock.accept()

    try:
        # Receive the data in small chunks and retransmit it
        while True:
            data = connection.recv(64)
            print 'received "%s"' % data

            # initialize motor and get current position
            if "INIT_" in data and init == False:
                init = True
                o = OwisControl.owis()                
                o.init()
                curPos = o.checkInit()                
                connection.sendall(curPos[0] + "," + curPos[1] + "," + curPos[2])

            # perform reference run
            if "REFR_" in data and init == True:
                o.ref() 
                o.writeLog()
                connection.sendall("0,0,0")

            # move to absolute position  
            elif "MOVA_" in data and init == True:
                newPos = data[5:].split(",")
                newPos = o.len_to_ink(newPos, "um")
                o.checkRange(newPos[0],newPos[1],newPos[2],"Abs")
                curPos = o.moveAbs(newPos[0],newPos[1],newPos[2])
                o.writeLog()
                connection.sendall(curPos[0] + "," + curPos[1] + "," + curPos[2])

#                o.test_drive("\Speedtest.txt")                
#                connection.sendall("6,6,6") 

            elif "MOVR_" in data and init == True:
                newPos = data[5:].split(",")              
                newPos = o.len_to_ink(newPos, "um")                
                o.checkRange(newPos[0],newPos[1],newPos[2],"Rel")
                curPos = o.moveRel(newPos[0],newPos[1],newPos[2])
                o.writeLog()
                connection.sendall(curPos[0] + "," + curPos[1] + "," + curPos[2])

            # absolute probe station movement with z-drive
            elif "MOPA_" in data and init == True:
                newPos = data[5:].split(",")              
                o.checkRange(newPos[0],newPos[1],newPos[2],"Abs")
                o.probe_moveAbs(newPos[0],newPos[1],newPos[2])

                            
            elif "MOPR_" in data and init == True:
                newPos = data[5:].split(",")              
                o.checkRange(newPos[0],newPos[1],newPos[2],"Abs")
                o.probe_moveAbs(newPos[0],newPos[1],newPos[2])


            # turn off motor and write position to log file            
            elif "STOP_" in data:
                o.writeLog()
                o.motorOff() 
                connection.sendall("1,1,1")  
            else:              
                print 'no more data from', client_address
                break

    finally:
        # Clean up the connection
        connection.close()
