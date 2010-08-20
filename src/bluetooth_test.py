
# Standard Imports
import sys
import optparse

# Library import
import serial

# Project Imports
import proto.messages_robocup_ssl_detection_pb2 as ssl_detect
import proto.messages_robocup_ssl_wrapper_pb2 as ssl_wrapper
import messages

def open_port(devfile):
    port = serial.Serial()
    port.setPort(devfile)
    port.setBaudrate(9600)
    port.setStopbits(1)
    port.setByteSize(8)
    port.setTimeout(500)
    port.setParity('N')
    port.open()
    return port

def basic_test(port):
    print 'Read:',port.read(5)
    msg = 'Hello, Robot!'
    port.write(msg)
    print '"%s" sent' % msg

def full_test(port):
    field_info = messages.make_test_detectionframe()
    print 'Sending full packet:\n',field_info
    field_info.send_data(port)
    print 'sent'

def main(argv=None):
    if argv is None:
        argv = sys.argv

    # Parse arguments
    parser = optparse.OptionParser()
    parser.set_defaults(devfile="/dev/rfcomm0", fulltest = False)
    parser.add_option("-d", "--dev", dest="devfile",
                      help="Device file the NXT is connected to")
    parser.add_option("-f", "--fulltest",  action="store_true", dest="fulltest",
                      help="Send a test packet to python")
    (options, args) = parser.parse_args()
    
    port = open_port(options.devfile)

    if options.fulltest:
        full_test(port)
    else:
        basic_test(port)

    port.close()

if __name__ == "__main__":
    sys.exit(main())
