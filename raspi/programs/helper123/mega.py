class Pin:
    def __init__(self):
        self.mode = 10
        self.state = "not ready"
        self.data = None
    
    # reads data if available, otherwise returns -1
    def getReadResult(self):
        # check if digital and ready
        if self.mode is not 0 or self.state is not "ready":
            return -1

        # return data
        return self.data

    # sets pin to represent the start of a new reading
    def startRead(self):
        self.state = "not ready"

    # updates a pin with a reading result
    def set(self, data):
        self.data = data

# represents an Arduino Mega and all of its I/O
class Mega:
    # pin array
    pins = [Pin()] * 70

    # initializes a pin
    def initializePin(self, pin, value):
        # check for valid pin
        if pin < 0 or pin >= 70:
            print("Error: Invalid pin number")
            return

        self.pins[pin].mode = value

    # gets the state of a pin
    def getPinState(self, pin):
        return self.pins[pin].state

    # reads a pin
    def getPinData(self, pin):
        return self.pins[pin].data

    # updates a pin's data and marks it as ready
    def setPinData(self, pin, data):
        self.pins[pin].data = data
        self.pins[pin].state = "ready"

    # marks a pin as not ready
    def setPinNotReady(self, pin):
        self.pins[pin].state = "not ready"

