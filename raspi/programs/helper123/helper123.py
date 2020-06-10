from packets import PACKET
from mega_spi import MegaSpi
from mega import Mega
import time

mega = MegaSpi()

# initializes connection
def init():
    mega.setupConnection()

# waits for the given time in milliseconds
def wait(ms):
    time.sleep(ms / 1000.0)

# processes incoming data
def update():
    mega.processSerial()

# measures the time taken for a message to travel round trip
def ping():
    delay = mega.ping()
    if(delay < 0):
        print("Error: No response")
    else:
        print("Ping time: " + str(delay))

# turns on the onboard Arduino LED
def ledOn():
    mega.safeSendPacket(PACKET["LED_HIGH"], None)

# turns off the onboard Arduino LED
def ledOff():
    mega.safeSendPacket(PACKET["LED_LOW"], None)

# initializes a pin for digital reading
def initPinDigitalRead(pin):
    mega.setPinDigitalRead(pin)

# gets the value of a digital pin
def digitalRead(pin):
    if(pin < 0 or pin > 49):
        print("Error: Invalid pin")
        return -1

    mega.safeSendPacket(PACKET["DIGITAL_READ"], [pin])
    while(mega.localMega.getPinState(pin) != "ready"):
        mega.processSerial()
    return mega.localMega.getPinData(pin)

