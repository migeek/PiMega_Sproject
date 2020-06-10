#ifndef PACKETS_H
#define PACKETS_H

// TODO: update to match largest packet size as necessary
#define PACKET_MAX_SIZE     (100)

// op codes
#define POP_DIGITAL_DATA    (0b11101111)
#define POP_DIGITAL_READ    (0b00010000)
#define POP_ERROR           (0b11111111)
#define POP_LED_HIGH        (0b01010101)
#define POP_LED_LOW         (0b10101010)
#define POP_PIN_INIT        (0b11110000)
#define POP_PIN_ACK         (0b00001111)
#define POP_PING            (0b00011000)
#define POP_RESET           (0b11000000)
#define POP_STARTUP         (0b11000001)
#define POP_REQUEST         (0b00010111)

// error codes
#define ERR_INVALID_PACKET  (0b00000010)
#define ERR_INVALID_PIN     (0b00000001)

#endif
