
# Standard Imports
import sys
import optparse

# Library import
import serial

# Project Imports
import proto.messages_robocup_ssl_detection_pb2 as ssl_detect
import proto.messages_robocup_ssl_wrapper_pb2 as ssl_wrapper

def openPort(devfile):
    port = serial.Serial()
    port.setPort(devfile)
    port.setBaudrate(9600)
    port.setStopbits(1)
    port.setByteSize(8)
    port.setTimeout(500)
    port.setParity('N')
    port.open()
    return port

def main(argv=None):
    if argv is None:
        argv = sys.argv

    # Parse arguments
    parser = optparse.OptionParser()
    parser.set_defaults(devfile="/dev/rfcomm0")
    parser.add_option("-d", "--dev", dest="devfile",
                      help="Device file the NXT is connected to")
    (options, args) = parser.parse_args()

    port = openPort(options.devfile)

    print port.read(5)

    port.write('Hello, Robot!')

    port.close()

if __name__ == "__main__":
    sys.exit(main())
