class OwisError(Exception):
    pass

class ComError(OwisError):
    def __init__(self, message):
        print(message)
    

class MotorError(OwisError):
    def __init__(self, message):
        print(message)


class SynchError(OwisError):
    def __init__(self, message):
        print(message)



# ErrorValues:

#-1	: "CommunicationError: Comport is already claimed or can not be found"
#-2	: "CommunicationError: Could not get proper position information in time."
#-3	: "SynchronizationError: Unexpected axis positions. Motor needs to be calibrated."
#-4	: "SynchronizationError: Display counter and motor position are unequal."
#-5	: "SynchronizationError: Motor position and position from log file are unequal."
#-6	: "MotorError: Destination is out of motor range!"
#-8	: "MotorError: Probe station movement is not possible without a 1000mu z-drive offset!"
#-9	: "MotorError: Probe station movement is only allowed in the xy-plane for saftey reasons!"



