#ifndef PINS_H
#define PINS_H

#define NUM_PINS        (70)
#define PIN_S_UNUSED    (10)
#define PIN_S_LOCKED    (11)
#define PIN_S_DIG_IN    (1)
#define PIN_S_DIG_OUT   (2)

// represents a pin
struct Pin {
  uint8_t state;
};

#endif
