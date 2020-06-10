from helper123.helper123 import *

def setup():
    init()
    initPinDigitalRead(8)

def loop():
    value = digitalRead(8)
    print(value)
    wait(100)

def main():
    setup()

    while(True):
        loop()
        update()

if __name__ == "__main__":
    main()

