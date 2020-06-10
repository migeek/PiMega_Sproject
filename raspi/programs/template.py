from helper123.helper123 import *

def setup():
    init()

    # Replace with your setup code here
    print("This is a line of setup code")

def loop():
    # Replace with your looping code here
    print("This is a line of loop code")
    wait(1000)

def main():
    setup()

    while(True):
        loop()
        update()

if __name__ == "__main__":
    main()

