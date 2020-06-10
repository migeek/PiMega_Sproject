#include <avr/wdt.h>
#include <SPI.h>
#include "packets.h"
#include "pins.h"

#define DEBUG     (true) // toggles Mega serial debug output
#define SEND_EN   (49)
#define BUF_SIZE  (100)

// transmission states
#define NO_DATA   (0)
#define DATA      (1)
#define REQUEST   (2)

struct Pin pins[NUM_PINS]; // must be global to be accessed in setup and loop

// SPI communication buffers
volatile uint8_t inputBuf[BUF_SIZE];
volatile uint16_t inputBufStart;          // position of first byte in buffer
volatile uint16_t inputBufLen;            // number of bytes in buffer
volatile uint8_t outputBuf[BUF_SIZE];
volatile uint16_t outputBufStart;         // position of first byte in buffer
volatile uint16_t outputBufLen;           // number of bytes in buffer
volatile uint8_t outputState;            // transmission state

// set up board
void setup() {
  // initialize debug serial
  Serial.begin(115200);
  printDebug("Booting up");

  // initialize spi
  pinMode(50, OUTPUT);
  pinMode(SEND_EN, OUTPUT);
  digitalWrite(SEND_EN, LOW);
  inputBufStart = 0;
  inputBufLen = 0;
  outputBufStart = 0;
  outputBufLen = 0;
  outputState = NO_DATA;
  SPCR |= _BV(SPE); // spi slave mode
  SPCR |= _BV(SPIE); // turn on interrupt

  // initialize builtin LED
  pinMode(LED_BUILTIN, OUTPUT);

  // initialize pin structure
  setupPins();

  // send startup packet
  sendPacket(POP_STARTUP, NULL, 0);
}

// spi interrupt routine
ISR(SPI_STC_vect) {
  uint8_t c = SPDR;

  // if data has been requested, send it
  if (outputState == REQUEST) {
    if (outputBufLen == 0) {
      outputState = NO_DATA;
      return;
    }

    SPDR = outputBuf[outputBufStart % BUF_SIZE];
    outputBufStart++;
    if (outputBufStart == BUF_SIZE) {
      outputBufStart = 0;
    }
    outputBufLen--;
    return;
  }

  // check for buffer overflow
  if (inputBufLen >= BUF_SIZE) {
    Serial.write("Error: SPI buffer overflow\n");
    return;
  }

  // add to end of buffer
  inputBuf[(inputBufStart + inputBufLen) % BUF_SIZE] = c;
  inputBufLen++;
}

// loop through main functions
void loop() {
  processSPI();

  // TODO: add other core loop functions here
  //    - motor control
  //    - long-read sensor data
  //    - LCD communication
}

// initialize pin structure
void setupPins() {
  for (int i = 0; i < NUM_PINS; i++) {
    if (i >= 49) {
      // pins used for communication
      pins[i].state = PIN_S_LOCKED;
    }
    else {
      pins[i].state = PIN_S_UNUSED;
    }
  }
}

// process spi packets until no more are available
void processSPI() {
  static uint8_t packetData[PACKET_MAX_SIZE];
  static uint8_t packetLen = 0;
  uint8_t pinNum;

  // process data until none available
  while (inputBufLen > 0) {
    // read next byte
    packetData[packetLen] = inputBuf[inputBufStart % BUF_SIZE];
    packetLen++;
    inputBufStart++;
    if (inputBufStart == BUF_SIZE) {
      inputBufStart = 0;
    }
    inputBufLen--;

    // report new packet
    if (packetLen == 1) {
      printDebug("New op code: " + String(packetData[0]));
    }

    // switch on op code
    switch (packetData[0]) {
      case POP_LED_HIGH:
        digitalWrite(LED_BUILTIN, HIGH);
        printDebug("LED high");

        packetLen = 0; // end of packet
        break;

      case POP_LED_LOW:
        digitalWrite(LED_BUILTIN, LOW);
        printDebug("LED low");

        packetLen = 0; // end of packet
        break;

      case POP_PING:
        // respond to ping
        sendPacket(POP_PING, NULL, 0);
        printDebug("Responded to ping");

        packetLen = 0;
        break;

      case POP_PIN_INIT:
        processPinInit(&packetLen, packetData);
        break;

      case POP_DIGITAL_READ:
        processDigitalRead(&packetLen, packetData);
        break;

      case POP_RESET:
        printDebug("Received reset");
        delay(100); // delay to allow debug print
        reboot();

      case POP_REQUEST:
        processRequest(&packetLen);
        break;

      // TODO: add other packet types here

      default:
        // invalid packet, send error and discard
        uint8_t errorCode = ERR_INVALID_PIN;
        sendPacket(POP_ERROR, &errorCode, 1);
        printDebug("Invalid op code " + String(packetData[0]));

        packetLen = 0; // discard op code
    }
  }
}

// initializes a pin from a packet
void processPinInit(uint8_t* packetLen, uint8_t* packetData) {
  // skip processing if incomplete packet
  if (*packetLen < 3) {
    return;
  }

  uint8_t pinNum = packetData[1];

  // check pin is unused
  if (pins[pinNum].state != PIN_S_UNUSED) {
    // return error message
    uint8_t errorCode[2] = {ERR_INVALID_PIN, pinNum};
    sendPacket(POP_ERROR, errorCode, 2);
    printDebug("Failed to initialize pin");

    *packetLen = 0;
    return;
  }

  // initialize pin
  pins[pinNum].state = packetData[2];
  pinMode(pinNum, packetData[2]);

  // send ack
  sendPacket(POP_PIN_ACK, NULL, 0);

  *packetLen = 0; // end of packet
}

// reads a pin from a packet
void processDigitalRead(uint8_t* packetLen, uint8_t* packetData) {
  // skip processing if incomplete packet
  if (*packetLen < 2) {
    return;
  }

  uint8_t pinNum = packetData[1];

  // check for valid pin
  if (pins[pinNum].state != INPUT) {
    // return error message
    uint8_t errorCode[2] = {ERR_INVALID_PIN, pinNum};
    sendPacket(POP_ERROR, errorCode, 2);
    printDebug("Failed to initialize pin");

    *packetLen = 0;
    return;
  }

  // send response
  uint8_t value[2];
  value[0] = pinNum;
  value[1] = digitalRead(pinNum);
  sendPacket(POP_DIGITAL_DATA, value, 2);

  *packetLen = 0; // end of packet
}

// processes a data request
void processRequest(uint8_t* packetLen) {
  // wait until not sending data to raspi
  while (outputState == REQUEST);

  SPCR &= ~(_BV(SPIE)); // turn off spi interrupt
  SPDR = outputBufLen;
  outputState = REQUEST;
  digitalWrite(SEND_EN, LOW);
  SPCR |= _BV(SPIE); // turn on spi interrupt

  // wait until not sending data to raspi
  while (outputState == REQUEST);

  *packetLen = 0; // end of packet
}

// add a byte to output buffer
void addToOutput(uint8_t msgByte) {
  if (outputBufLen >= BUF_SIZE) {
    printDebug("Error: Buffer overflow");
    return;
  }

  outputBuf[(outputBufStart + outputBufLen) % BUF_SIZE] = msgByte;
  outputBufLen++;
}

// queues a packet to be sent to the raspi
void sendPacket(uint8_t opCode, uint8_t* msg, uint8_t msgLen) {
  uint8_t i;
  // wait until not sending data to raspi
  while (outputState == REQUEST);

  SPCR &= ~(_BV(SPIE)); // turn off spi interrupt

  // write in op code and message
  addToOutput(opCode);
  for (i = 0; i < msgLen; i++) {
    addToOutput(msg[i]);
  }

  digitalWrite(SEND_EN, HIGH);
  outputState = DATA;

  SPCR |= _BV(SPIE); // turn on spi interrupt
}

// prints a debug message if debugging is enabled
static inline void printDebug(String str) {
  if (DEBUG) {
    Serial.println(str);
  }
}

// software reboots the Arduino
void reboot() {
  wdt_disable();
  wdt_enable(WDTO_15MS);
  while (1);
}
