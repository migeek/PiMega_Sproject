from helper123.helper123 import *

def setup():
    print("Starting program")
    init()
    print("Finished setup")

def loop():
    ping()
    wait(1000)

def main():
    setup()

    while(True):
        loop()
        update()

if __name__ == "__main__":
    main()

