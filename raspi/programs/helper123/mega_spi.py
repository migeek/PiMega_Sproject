import array
import serial
import time
import packets
import struct
import spidev
import RPi.GPIO as GPIO
from mega import Mega

# connects to an Arduino Mega for controlling a robot
class MegaSpi:
    # constants
    BAUD_RATE = 19200

    # spi connection object
    spi = None

    # spi transmission
    rxData = []

    # virtual Mega tracking object
    localMega = None

    # byte array for reading packets
    packet = bytearray(packets.MAX_PACKET_LENGTH)
    packetLength = 0

    # ping response tracker
    pingResponse = False

    # pin initialization check
    pinInitSafe = None

    # connects to arduino
    def setupConnection(self):
        self.spi = spidev.SpiDev()
        self.spi.open(0,0)
        self.spi.max_speed_hz = 100000
        time.sleep(0.3) # wait to be safe

        # set up SEND_EN pin for receiving data
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(25, GPIO.IN)

        # reset mega
        self.sendPacket(packets.PACKET["RESET"], None)
        time.sleep(1.5) # wait to allow bootup

    def requestData(self):
        self.sendPacket(packets.PACKET["REQUEST"], None)

        # block until response
        while(GPIO.input(25)):
            pass
        
        # read data size
        dataSize = self.spi.readbytes(1)[0]

        # loop transfer for data size
        for i in range(dataSize):
            rx = self.spi.readbytes(1)[0]
            self.rxData.append(rx)

    # processes all available serial data
    def processSerial(self):
        # check if connection has been set up
        if self.spi is None:
            print("Error: SPI connection not initialized")
            return

        # poll SEND_EN for incoming data
        if(GPIO.input(25)):
            self.requestData()

        # read data as long as it is available
        while len(self.rxData) > 0:
            # read next byte
            self.packet[self.packetLength] = self.rxData[0]
            self.packetLength += 1
            self.rxData.pop(0)

            # switch on packet type
            if self.packet[0] == packets.PACKET["ERROR"]:
                self.processError()

            elif self.packet[0] == packets.PACKET["DIGITAL_DATA"]:
                if self.packetLength < 3:
                    continue
                
                self.processDigitalData()

            elif self.packet[0] == packets.PACKET["PING"]:
                self.processPing()

            elif self.packet[0] == packets.PACKET["PIN_ACK"]:
                self.processPinAck()

            elif self.packet[0] == packets.PACKET["STARTUP"]:
                self.processStartup()
               
            # TODO: add other packet types here

            else:
                # report bad packet and throw out data
                print("Error: Unrecognized op code " + str(self.packet[0]))
                self.packetLength = 0

    def processDigitalData(self):
        # update pin structure
        self.localMega.setPinData(self.packet[1], self.packet[2])

        # reset after complete packet
        self.packetLength = 0

    def processPing(self):
        # mark ping response as received
        self.pingResponse = True

        # reset after complete packet
        self.packetLength = 0

    def processPinAck(self):
        # update pin initialization state
        self.pinInitSafe = True

        # reset after complete packet
        self.packetLength = 0

    def processStartup(self):
        # check if mega is already initialized
        if self.localMega is not None:
            print("Error: Mega reset")
            exit()

        # initialize local mega
        self.localMega = Mega()

        # reset after complete packet
        self.packetLength = 0

    # reports an error
    def processError(self):
        # check for error message contents
        if self.packetLength < 2:
            return
        # check errors of length 2
        elif self.packetLength == 2:
            if self.packet[1] == packets.ERROR["INVALID_PACKET"]:
                print("Error: Arduino did not recognize packet")
                # reset after complete packet
                self.packetLength = 0
        # check errors of length 3
        elif self.packetLength == 3:
            if self.packet[1] == packets.ERROR["INVALID_PIN"]:
                print("Error: Invalid pin " + str(self.packet[2]))
                self.pinInitSafe = False
                # reset after complete packet
                self.packetLength = 0

        # TODO: add other errors here
        
        # unrecognized error
        else:
            print("Error: Unrecognized error message")

    # sends a packet to the Arduino
    def sendPacket(self, opCode, msg):
        self.spi.writebytes([opCode])
        if not msg is None:
            self.spi.xfer(msg)

    # checks for incoming data before sending a packet to the Arduino
    def safeSendPacket(self, opCode, msg):
        # check for incoming data to avoid overwriting messages
        self.processSerial()

        self.sendPacket(opCode, msg)

    # sets up a pin for digital reading
    def setPinDigitalRead(self, pin):
        # reset pin init state
        self.pinInitSafe = None

        # send request to Mega
        data = bytearray()
        data.append(pin)
        data.append(0)
        self.safeSendPacket(packets.PACKET["PIN_INIT"], data)

        # wait for ack or error
        while(self.pinInitSafe is None):
            self.processSerial()

        # check for error
        if not self.pinInitSafe:
            exit()

        # update local Mega
        self.localMega.initializePin(pin, 0)

    # sends a ping to the Arduino and returns the response time in decimal seconds or -1 on error
    def ping(self):
        # check if connection has been set up
        if self.spi is None:
            print("Error: SPI connection not initialized")
            return

        # reset ping tracker and start timer
        self.pingResponse = False
        start = time.time()
        end = time.time()

        # send ping
        self.safeSendPacket(packets.PACKET["PING"], None)

        # block until response or 1 second elapsed
        while((not self.pingResponse) and (end < start + 1)):
            self.processSerial()
            end = time.time()

        # check for timeout
        if end >= start + 1:
            return -1

        # return elapsed time
        return end - start

