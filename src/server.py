
# Python Imports
import threading
import Queue
import sys
import optparse
import struct
import socket
import os

# Project Imports
import messages
import proto.messages_robocup_ssl_wrapper_pb2 as ssl_wrapper

# Library Imports
import pyinotify

X_SHIFT = 121.92;
Y_SHIFT = 121.92/2.0;
SCALE = 0.1;

class FieldUpdateConsumer(threading.Thread):
    """
    Grabs new SSL_DetectionFrame packets off its queue and sends them for
    processing until its told to stop
    """

    def start(self):
        self._lock = threading.Lock()
        self._running = True
        # Infinite size FIFO queue (insertion never blocks)
        self._queue = Queue.Queue(maxsize = 0)

        # Start thread
        threading.Thread.start(self)

    def running(self):
        running = None
        self._lock.acquire()
        running = self._running
        self._lock.release()
        return running

    def set_running(self, running):
        self._lock.acquire()
        self._running = running
        self._lock.release()

    def put(self,frame):
        self._queue.put_nowait(frame)

    def run(self):
        while self.running():
            frame = None
            try:
                # Wait on an frame
                frame = self._queue.get(block = True, timeout = 0.1)

                # Empty the queue leaving us with the last (and most recent
                # frame)
                while not self._queue.empty():
                    frame = self._queue.get_nowait()
                
            except Queue.Empty:
                pass

            # Now lets process this frame, only if we are still running
            if self.running():
                if frame is not None:
                    self.process_frame(frame)

    def process_frame(self, frame):
        """
        Over ride this to process frame events
        """
        pass

class DebugConsumer(FieldUpdateConsumer):
    """
    Grabs frames and prints them
    """

    def process_frame(self, frame):
        #print messages.FieldInfo(frame,X_SHIFT,Y_SHIFT,SCALE)
        pass

class BluetoothConsumer(FieldUpdateConsumer):
    """
    Consumes frames and writes out on the given port
    """
    
    def start(self, devfile, testmode = False):
        if not testmode:
            self.port = self._open_port(devfile)
        else:
            self.port = open(devfile,'w')
        FieldUpdateConsumer.start(self)

    def process_frame(self, frame):
        if self.port is not None:
            field_info = messages.FieldInfo(frame,X_SHIFT,Y_SHIFT,SCALE)
            field_info.send_data(self.port)
            self.port.flush()

    def _open_port(devfile):
        port = serial.Serial()
        port.setPort(devfile)
        port.setBaudrate(9600)
        port.setStopbits(1)
        port.setByteSize(8)
        port.setTimeout(500)
        port.setParity('N')
        port.open()
        return port    

class ConsumerPool(object):
    """
    Manages all our consumer threads which push data to serial port or screen
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._consumers = []

    def add_consumer(self, consumer):
        self._lock.acquire()
        self._consumers.append(consumer)
        self._lock.release()

    def remove_consumer(self, consumer):
        self._lock.acquire()
        self._consumers.remove(consumer)
        self._lock.release()

    def stop_all(self):
        self._lock.acquire()
        for consumer in self._consumers:
            consumer.set_running(False)
        self._lock.release()

    def join_all(self):
        self._lock.acquire()
        for consumer in self._consumers:
            consumer.join()
        self._lock.release()

    def put(self, frame):
        self._lock.acquire()
        for consumer in self._consumers:
            consumer.put(frame)
        self._lock.release()
    
# TODO: bluetooth consumer

# TODO: some kind of system which spawns those consumers as they appear

class BluetoothDevWatcher(pyinotify.ProcessEvent):
    """
    Watches the device directory, and create BluetoothConsumers for new devices
    """
    
    def __init__(self, prefix, pool, testmode = False):
        pyinotify.ProcessEvent.__init__(self)

        self._pool = pool
        self._prefix = prefix
        self._blueConsumers = {}
        self._testmode = testmode

    def process_IN_CREATE(self, event):
        print "Created",event.path,event.name,'pre:',self._prefix
        if str(event.name).startswith(self._prefix):
            full_path = os.path.join(event.path, event.name)
            print "Connecting to:",full_path
            
            # Create and store the consumer for future shutdown
            blue_con = BluetoothConsumer()
            self._blueConsumers[full_path] = blue_con

            # Start up and add to the pool
            blue_con.start(full_path, self._testmode)
            self._pool.add_consumer(blue_con)

    def process_IN_DELETE(self, event):
        """
        Tries to find the currently created consumer for this device and
        shut it down if needed
        """
        full_path = os.path.join(event.path, event.name)
        if full_path in self._blueConsumers:
            print "Removing:",full_path
            blue_con = self._blueConsumers[full_path]
            blue_con.set_running(False)
            self._pool.remove_consumer(blue_con)
            blue_con.join()


def open_mcast_socket(ip_addr_str, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', port))
    mreq = struct.pack("=4sl", socket.inet_aton(ip_addr_str), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    return sock


def main(argv=None):
    if argv is None:
        argv = sys.argv

    # Parse arguments
    parser = optparse.OptionParser()
    parser.set_defaults(host="224.5.23.2", port= 10002)
    parser.add_option("-H", "--host", dest="hostname",
                      type="string", help="specify UDP multicast ip address")
    parser.add_option("-p", "--port", dest="portnum",
                      type="int", help="port number to run on")
    (options, args) = parser.parse_args()
    
    # Open up the UDP multicast
    sock = open_mcast_socket(options.host, options.port)

    # Consumer pool
    pool = ConsumerPool()
    
    # Create the debug consumer
    debug = DebugConsumer()
    pool.add_consumer(debug)

    # Create the watcher
    mask = pyinotify.EventsCodes.IN_DELETE | pyinotify.EventsCodes.IN_CREATE
    wm = pyinotify.WatchManager()

    blueWatcher = BluetoothDevWatcher('bob', pool, testmode = True)
    notifier = pyinotify.ThreadedNotifier(wm, blueWatcher)

    wdd = wm.add_watch('/tmp/blue', mask, rec=False)

    # Start the theads!!
    notifier.start()
    debug.start()

    wrapper_packet = ssl_wrapper.SSL_WrapperPacket()
    try:
        while 1:
            data, sender = sock.recvfrom(1500)

            wrapper_packet.ParseFromString(data)
            frame = wrapper_packet.detection
            pool.put(frame)
            
    except KeyboardInterrupt:
        pool.stop_all()
        pool.join_all()

if __name__ == "__main__":
    sys.exit(main())
