from helper123.helper123 import *

def setup():
    print("Starting program")
    init()
    print("Finished setup")

def loop():
    ledOn()
    wait(500)

    ledOff()
    wait(500)

def main():
    setup()

    while(True):
        loop()
        update()

if __name__ == "__main__":
    main()

