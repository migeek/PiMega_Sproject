import time
from packets import PACKET
from mega_spi import MegaSpi
from mega import Mega

# sets up a connection and sends some commands
# - sets up pin 8 for digital reading
# - sends requests to pin 8 and monitors when data is available
def main():
    # create objects
    mega = MegaSpi()

    # initialize connection to Arduino
    mega.setupConnection()

    while(True):
        # send a ping and print the result
        pingTime = mega.ping()
        print("Ping time: " + str(pingTime))
        time.sleep(1)

if __name__ == "__main__":
   main()

