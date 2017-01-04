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
                curPos = o.init()
                connection.sendall(curPos[0] + "," + curPos[1] + "," + curPos[2])

            # move to position  
            elif "MOVA_" in data and init == True:
                newPos = data[5:].split(",")
                temp = []
                for el in newPos:
                    el = int(el.replace("'",""))
                    temp.append(el)
                newPos = temp

                curPos = o.moveAbs(newPos[0],newPos[1],newPos[2])
#                connection.sendall(curPos[0] + "," + curPos[1] + "," + curPos[2])
#                o.test_drive("\Speedtest.txt")                
                connection.sendall("6,6,6")   
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
