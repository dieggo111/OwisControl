import socket
import sys, os
import OwisControl
import OwisError

server_name = "localhost"
port = 10000
inti_bool = False

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the port
server_address = (server_name, port)
print()
print('Python Motor Server for OWIS stages')
print('(c) IEKP, March 2017')
print()
print('Server listening on %s, port %s' % server_address)

# Bind socket sock with the server adress local host with port 10000
sock.bind(server_address)

# Listen for incoming connections
sock.listen(1)

while True:
    # Wait for a connection / press Ctrl+Break(Pause) to abort
    print()
    print('Waiting for a client connection...')
    connection, client_address = sock.accept()

    try:
        # Receive the data in small chunks and retransmit it
        while True:
            try:
                data = connection.recv(64)

                print('Received "%s" from %s' %(data.decode("utf-8"),
                      client_address))

                # initialize motor and get current position
                if "INIT" in data.decode("utf-8") and init_bool == False:
                    o = OwisControl.owis("PS10",
                                         "/dev/ttyACM0",
                                         "/dev/ttyACM1",
                                         "/dev/ttyACM2")
                    o.init()
                    o.checkInit()
                    curPos = o.getPos()
                    connection.sendall(bytes("OK_" + curPos[0] + "," \
                                             + curPos[1] + "," \
                                             + curPos[2], "utf-8"))
                    inti_bool = True
                    break

                elif "INIT" in data.decode("utf-8") and init_bool == True:
                    curPos = o.getPos()
                    connection.sendall(bytes("OK_" + curPos[0] + "," \
                                       + curPos[1] + "," \
                                       + curPos[2], "utf-8"))

                # perform reference run
                elif "REFDRIVE" in data.decode("utf-8") and init_bool == True:
                    o.ref()
                    curPos = o.getPos()
                    o.writeLog()
                    connection.sendall(bytes("OK_" + curPos[0] + "," + curPos[1] + "," + curPos[2], "utf-8"))

                # move to absolute position
                elif "MOVA_" in data.decode("utf-8"):
                    newPos = data[5:].decode("utf-8").split(",")
                    newPos = o.len_to_ink(newPos, "um")
                    o.checkRange(newPos[0],newPos[1],newPos[2],"Abs")
                    o.moveAbs(newPos[0],newPos[1],newPos[2])
                    curPos = o.getPos()
                    o.writeLog()
                    connection.sendall(bytes("OK," + curPos[0] + "," + curPos[1] + "," + curPos[2], "utf-8"))

                elif "MOVR_" in data.decode("utf-8"):
                    newPos = data[5:].decode("utf-8").split(",")
                    newPos = o.len_to_ink(newPos, "um")
                    o.checkRange(newPos[0],newPos[1],newPos[2],"Rel")
                    o.moveRel(newPos[0],newPos[1],newPos[2])
                    curPos = o.getPos()
                    o.writeLog()
                    connection.sendall(bytes("OK," + curPos[0] + "," + curPos[1] + "," + curPos[2], "utf-8"))

                # absolute probe station movement with z-drive
                elif "MOPA_" in data.decode("utf-8"):
                    newPos = data[5:].decode("utf-8").split(",")
                    o.checkRange(newPos[0],newPos[1],newPos[2],"Abs")
                    o.probe_moveAbs(newPos[0],newPos[1],newPos[2])
                    curPos = o.getPos()
                    o.writeLog()
                    connection.sendall(bytes("OK," + curPos[0] + "," + curPos[1] + "," + curPos[2], "utf-8"))


                elif "MOPR_" in data.decode("utf-8"):
                    newPos = data[5:].decode("utf-8").split(",")
                    o.checkRange(newPos[0],newPos[1],newPos[2],"Abs")
                    o.probe_moveAbs(newPos[0],newPos[1],newPos[2])
                    curPos = o.getPos()
                    o.writeLog()
                    connection.sendall(bytes("OK," + curPos[0] + "," + curPos[1] + "," + curPos[2], "utf-8"))

#                # turn off motor and write position to log file
#                elif "STOP" in data.decode("utf-8"):
#                    o.writeLog()
#                    o.motorOff()
#                    connection.sendall(bytes("OK,-1,-1,-1", "utf-8"))

                elif "PS10R_" in data.decode("utf-8"):
                    newPos = data[6:].decode("utf-8").split(",")
                    o.checkRange(newPos[0],newPos[1],newPos[2],"Abs")
                    o.PS10_moveRel(newPos[0],newPos[1],newPos[2])
                    curPos = o.getPos()
                    o.writeLog()
                    connection.sendall(bytes("OK," + curPos[0] + "," + curPos[1] + "," + curPos[2], "utf-8"))
                else:
                    print ('No more data from %s' %str(client_address[0]))
                    break

            except (KeyboardInterrupt):
                print("inner")
                raise


    except OwisError.ComError:
        connection.sendall(bytes("ER,123", "utf-8"))

    except OwisError.SynchError:
        connection.sendall(bytes("ER,124", "utf-8"))

    except OwisError.MotorError:
        connection.sendall(bytes("ER,125", "utf-8"))

    # Catch the Ctrl-C event
    except (KeyboardInterrupt, SystemExit):
        print('Ctrl-C pressed, stopping server...')
        raise

    finally:
        # turn off motor and write position to log file
        o.writeLog()
        o.motorOff()
        connection.sendall(bytes("OK,-1,-1,-1", "utf-8"))
        # Clean up the connection
        connection.close()
