import socket
import sys, os
import OwisControl_PS10
import OwisError

server_name = "localhost"
port = 10000
init_done = False
comList = ["INIT", "REFDRIVE", "GETPOS", "GETSTAT", "STOP",
           "MOVR_", "MOPR_", "MOVA_", "MOPA_"]

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the port
server_address = (server_name, port)
print()
print('Python Motor Server for OWIS stages')
print('(c) IEKP, March 2017')
print()
print('Server listening on %s, port %s' % server_address)
print()

# Bind socket "sock" with the server_address
sock.bind(server_address)

# Listen for incoming connections
sock.listen(1)

try:
    while True:
        # Wait for a connection / press Ctrl+Break(Pause) to abort
        print()
        print('Listening to socket...')
        connection, client_address = sock.accept()

        # Receive the data in small chunks and retransmit it
        try:
            # data = connection.recv(64)
            while True:
                data = connection.recv(64)

                if data.decode("utf-8") == "":
                    pass
                else:
                    print('Received "%s" from %s'
                          %(data.decode("utf-8"), client_address))

                # initialize motor and get current position
                if "INIT" in data.decode("utf-8") and init_done == False:
                    #TODO: Controller type and port names need to be variable
                    o = OwisControl_PS10.owis("/dev/ttyACM0",
                                              "/dev/ttyACM1",
                                              "/dev/ttyACM2")
                    o.init()
                    o.checkInit()
                    curPos = o.getPos("str")
                    connection.sendall(bytes("OK_" + curPos, "utf-8"))
                    init_done = True

                # if motor was already initialized before
                elif "INIT" in data.decode("utf-8") and init_done == True:
                    curPos = o.getPos("str")
                    print("Axes already initialized...")
                    connection.sendall(bytes("OK_" + curPos, "utf-8"))

                # perform reference run
                elif "REFDRIVE" in data.decode("utf-8") and init_done == True:
                    o.REFDRIVE()
                    curPos = o.getPos("str")
                    connection.sendall(bytes("OK_" + curPos, "utf-8"))

                # move to absolute position
                elif "MOVA_" in data.decode("utf-8") and init_done == True:
                    newPos = data[5:].decode("utf-8").split(",")
                    o.MOVA(newPos[0],newPos[1],newPos[2])
                    curPos = o.getPos("str")
                    connection.sendall(bytes("OK_" + curPos, "utf-8"))

                # move to relative position
                elif "MOVR_" in data.decode("utf-8") and init_done == True:
                    newPos = data[5:].decode("utf-8").split(",")
                    o.MOVR(newPos[0],newPos[1],newPos[2])
                    curPos = o.getPos("str")
                    connection.sendall(bytes("OK_" + curPos, "utf-8"))

                # absolute probe station movement (including z-drive)
                elif "MOPA_" in data.decode("utf-8") and init_done == True:
                    newPos = data[5:].decode("utf-8").split(",")
                    o.MOPA(newPos[0],newPos[1],newPos[2])
                    curPos = o.getPos("str")
                    connection.sendall(bytes("OK_" + curPos, "utf-8"))

                # relative probe station movement (including z-drive)
                elif "MOPR_" in data.decode("utf-8") and init_done == True:
                    newPos = data[5:].decode("utf-8").split(",")
                    o.MOPR(newPos[0],newPos[1],newPos[2])
                    curPos = o.getPos("str")
                    connection.sendall(bytes("OK_" + curPos, "utf-8"))

                # turn off motor and write position to log file
                elif "STOP" in data.decode("utf-8"):
                    curPos = o.getPos("str")
                    connection.sendall(bytes("OK_" + curPos, "utf-8"))
                    break

                # returns current position
                elif "GETPOS" in data.decode("utf-8") and init_done == True:
                    curPos = o.getPos("str")
                    connection.sendall(bytes("OK_" + curPos, "utf-8"))

                # returns current status
                elif "GETSTAT" in data.decode("utf-8") and init_done == True:
                    status = o.getStatus()
                    connection.sendall(bytes("ST_" + status, "utf-8"))

                # intercept invalid commands
                elif data.decode("utf-8") not in comList and data.decode("utf-8") != "":
                    connection.sendall(bytes("ER_666", "utf-8"))

                else:
                    print ('No more data from %s' %str(client_address[0]))
                    break

        except ValueError:
            connection.sendall(bytes("ER_126", "utf-8"))

        except OwisError.ComError:
            connection.sendall(bytes("ER_123", "utf-8"))

        except OwisError.SynchError:
            connection.sendall(bytes("ER_124", "utf-8"))

        except OwisError.MotorError:
            connection.sendall(bytes("ER_125", "utf-8"))

        finally:
            # close socket
            connection.close()

    # turn off motor and write position to log file
    if init_done == True:
        o.motorOff()
        o.writeLog()
    else:
        pass


# Catch the Ctrl-C event
except(KeyboardInterrupt):
    print()
    print("Server manually stopped by pressing Ctrl-C. Shutting down...")
    # turn off motor and write position to log file
    if init_done == True:
        o.writeLog()
        o.motorOff()
    else:
        pass

    # close socket
    connection.close()
