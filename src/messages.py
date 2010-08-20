
# Standard Imports
import struct
import unittest
import math
import StringIO

# Project Imports
import proto.messages_robocup_ssl_detection_pb2 as ssl_detection
import proto.messages_robocup_ssl_wrapper_pb2 as ssl_wrapper


__doc__ = """
This module defines the basic data structures that are sent over the wire. 
Each one has a pack function which packs its contents into a binary string
which the bluetooth device can read.
"""

# TODO: deal with signed heading floats!!!

# Free helper functions

#-----------------------------------------------------------------------------#
#                       H E L P E R   F U N C T I O N S                       #
#-----------------------------------------------------------------------------#

def compress_float(num):
    """
    Packs a floating point number with a value of 0.0 to 127.0, with a 
    percision of 0.5 into a single byte (max value 254)
    """
    raw_num = int(round(num*2.0))
    if raw_num > 254:
        res = 254
    else:
        res = raw_num
        
    return res

def uncompress_float(packedNum):
    """
    Reverse the effects of packing the float
    """
    return packedNum * 0.5    

def compress_int(num):
    """
    Packs the value as a norma int limited to a size of 254
    """
    if num > 254:
        return 254
    return int(round(num))

def uncompress_int(num):
    return num

def pack_angle(angle):
    """
    This packs the an angle with ~single degree precision into two bytes
    """
    # Remove "excess" angle (ie. extra multiples of 2pi)
    angle = angle % (2*math.pi)

    # Make the angle between -pi and pi
    if angle > math.pi:
        angle -= 2*math.pi

    # Scale the angle down into to down into 254 values
    scaled_angle = angle * (254/math.pi) / 2.0

    # Determine sign
    sign = 0
    if scaled_angle < 0:
        sign = 1

    return struct.pack('BB', sign, compress_float(math.fabs(scaled_angle)))

def unpack_angle(data, unpack_offset = 0):
    """
    This unpacks results from the angle compression
    """
    # Unpack and uncompress the data
    sign, raw_scaled_angle = struct.unpack_from('BB', data, 
                                                offset = unpack_offset)
    scaled_angle = uncompress_float(raw_scaled_angle)
    
    # Unscale the data from its scaled form
    angle = scaled_angle * (math.pi/254) * 2.0

    # The sign value designates negative numbers
    if sign:
        angle = -angle;

    return angle


#-----------------------------------------------------------------------------#
#                                C L A S S E S                                #
#-----------------------------------------------------------------------------#

class Vector2D(object):
    """
    Simple X,Y position
    """
    
    PACKED_SIZE = 2

    def __init__(self,x,y):
        self.x = x;
        self.y = y;

    def pack(self):
        """Returns the object encoded in a binary string"""
        return struct.pack('BB', 
                           compress_float(self.x),  
                           compress_float(self.y))

    @staticmethod
    def unpack(data, unpack_offset = 0):
        """Returns and object build from the packed data"""
        vec = Vector2D(0,0)
        raw_X, raw_Y = struct.unpack_from('BB',data, offset = unpack_offset)
        vec.x = uncompress_float(raw_X)
        vec.y = uncompress_float(raw_Y)
        return vec

    # Boiler plate methods
    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "(%f,%f)" % (self.x, self.y)

    def __eq__(self, other):
        if isinstance(other, Vector2D):
            return (self.x == other.x) and (self.y == other.y)
        return NotImplemented

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

# TODO: FINISH ME
class Ball(object):
    """
    Represents ball position and size over the wire
    """
    PACKED_SIZE = Vector2D.PACKED_SIZE + 1
    

class RobotInfo(object):
    """
    Describes the id, position, heading of a robot on the field
    """
    
    PACKED_SIZE = 1 + 2 + Vector2D.PACKED_SIZE

    def __init__(self, ID, heading, pos):
        self.id = ID
        self.heading = heading
        self.pos = pos

    def pack(self):
        """Returns the object encoded in a binary string"""
        id_data = struct.pack('B', compress_int(self.id))
        angle_data = pack_angle(self.heading)
        pos_data = self.pos.pack()
        return id_data + angle_data + pos_data

    @staticmethod
    def unpack(data, unpack_offset = 0):
        """Returns and object build from the packed data"""
        raw_data = struct.unpack_from('B',data, offset = unpack_offset)

        robotInfo = RobotInfo(0,0,0)
        robotInfo.id = uncompress_int(raw_data[0])
        robotInfo.heading = unpack_angle(data,
                                         unpack_offset = unpack_offset + 1)
        robotInfo.pos = Vector2D.unpack(data,
                                        unpack_offset = unpack_offset + 3)

        return robotInfo

    # Boiler plate methods
    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "RobotInfo(id:%d) %f:%s" % (self.id, self.heading, str(self.pos))

    def __eq__(self, other):
        if isinstance(other, RobotInfo):
            return (self.id == other.id) and (self.heading == other.heading) \
                and (self.pos == other.pos)
        return NotImplemented

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

class Header(object):
    """
    Includes the number of following RobotInfo and Vector2D ball positions
    """

    PACKED_SIZE = 2
    
    def __init__(self, num_robots, num_balls):
        self.num_robots = num_robots
        self.num_balls = num_balls

    def pack(self):
        data = struct.pack('BB',
                           compress_int(self.num_robots),
                           compress_int(self.num_balls))
        return data
    
    @staticmethod
    def unpack(data, unpack_offset = 0):
        raw_robot_num, raw_ball_num = struct.unpack_from('BB', data,
                                                         unpack_offset)

        header = Header(0,0)
        header.num_robots = uncompress_int(raw_robot_num)
        header.num_balls = uncompress_int(raw_ball_num)
        return header

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "Header(robo#: %d ball# %d)" % (self.num_robots, self.num_balls)


class FieldInfo(object):
    """
    Contains all the info about the robots and balls on the field
    """
    
    def __init__(self, detection_packet = None,
                 x_shift = 0, y_shift = 0, scale = 1):
        self.robots = []
        self.balls = []
        self.header = None
        self._x_shift = x_shift
        self._y_shift = y_shift
        self._scale = scale
        
        if detection_packet is not None:
            # Build up robots 
            for robot in detection_packet.robots_yellow:
                self.robots.append(RobotInfo(robot.robot_id, robot.orientation,
                                             self._parse_pos(robot)))

            for robot in detection_packet.robots_blue:
                self.robots.append(RobotInfo(robot.robot_id, robot.orientation,
                                             self._parse_pos(robot)))

            # Build up balls
            for ball in detection_packet.balls:
                # TODO: update me to include a ball object
                self.balls.append(self._parse_pos(ball))

            # Header
            self.header = Header(len(self.robots), len(self.balls))

    def _parse_pos(self, obj):
        return Vector2D((obj.x * self._scale) + self._x_shift,
                        (obj.y * self._scale) + self._y_shift)

    def send_data(self, fileobj):
        """
        Serializes and writes all the data to the given file descriptor
        """

        # Put everything in a big list, because the have the same interface,
        # and send into the file obj

        to_send = [self.header]
        to_send.extend(self.robots)
        to_send.extend(self.balls)
        
        # Send robots
        for item in to_send:
            data = item.pack()
            fileobj.write(data)

    @staticmethod
    def unpack(data):
        offset = 0
        field_info = FieldInfo()
        
        # Header
        field_info.header = Header.unpack(data)
        offset += Header.PACKED_SIZE
        
        # Robots
        for i in xrange(0, field_info.header.num_robots):
            field_info.robots.append(RobotInfo.unpack(data, offset))
            offset += RobotInfo.PACKED_SIZE

        # Balls
        for i in xrange(0, field_info.header.num_balls):
            field_info.balls.append(Vector2D.unpack(data, offset))
            offset += Vector2D.PACKED_SIZE

        return field_info

    def __str__(self):
        return self.__repr__()
        
    def __repr__(self):
        string_io = StringIO.StringIO()
        string_io.write("%s\n" % str(self.header))
        for robot in self.robots:
            string_io.write("%s\n" % robot)
        for ball in self.balls:
            string_io.write("Ball: %s\n" % ball)
        return string_io.getvalue()

#-----------------------------------------------------------------------------#
#                                T E S T S                                    #
#-----------------------------------------------------------------------------#

class TestFunctions(unittest.TestCase):
    def test_compress_float(self):
        self.assertEquals(10, compress_float(5.0))
        self.assertEquals(5, compress_float(2.5))

    def test_uncompress_float(self):
        self.assertEquals(7.5, uncompress_float(15))

    def test_float_compression(self):
        comp_float = compress_float(117.8)
        self.assertAlmostEqual(118, uncompress_float(comp_float),1)
        
    def test_compress_int(self):
        self.assertEqual(5, compress_int(5))
        self.assertEqual(254, compress_int(255))
        self.assertEqual(254, compress_int(655))

    def test_pack_angle(self):
        # Positive
        angle = math.pi * 7/10;
        data = pack_angle(angle)
        self.assertAlmostEqual(angle, unpack_angle(data), 2)

        # Negative
        angle = -math.pi * 3/10;
        data = pack_angle(angle)
        self.assertAlmostEqual(angle, unpack_angle(data), 2)

        # Wrap around
        data = pack_angle(math.pi * 1.5)
        self.assertAlmostEqual(-math.pi * 0.5, unpack_angle(data), 2)


class TestVector2D(unittest.TestCase):

    def test_pack_unpack(self):
        x = 3.5
        y = 6
        vec = Vector2D(x, y)
        data = vec.pack()

        vec2 = Vector2D.unpack(data)
        self.assertEqual(x, vec2.x)
        self.assertEqual(y, vec2.y)

    def test_equals(self):
        vec1 = Vector2D(1,2)
        vec2 = Vector2D(1,2)
        vec3 = Vector2D(1,3)
        vec4 = Vector2D(2,2)

        self.assertEquals(vec1,vec2)
        self.assertNotEquals(vec1,vec3)
        self.assertNotEquals(vec1,vec4)

class TestRobotPosInfo(unittest.TestCase):
    def test_pack_unpack(self):
        ID = 3
        heading = math.pi * 0.3
        pos = Vector2D(3.5, 6)

        robotInfo = RobotInfo(ID, heading, pos)
        data = robotInfo.pack()

        robotInfo2 = RobotInfo.unpack(data)
        self.assertEquals(ID, robotInfo2.id)
        self.assertAlmostEquals(heading, robotInfo2.heading, 2)
        self.assertEqual(pos, robotInfo2.pos)

    def test_equals(self):
        robo1 = RobotInfo(1, 8.5, Vector2D(2,3))
        robo2 = RobotInfo(1, 8.5, Vector2D(2,3))
        robo3 = RobotInfo(2, 8.5, Vector2D(2,3))
        robo4 = RobotInfo(1, 9.5, Vector2D(2,3))
        robo5 = RobotInfo(1, 8.5, Vector2D(3,3))

        self.assertEquals(robo1,robo2)
        self.assertNotEquals(robo1,robo3)
        self.assertNotEquals(robo1,robo4)
        self.assertNotEquals(robo1,robo5)

class TestHeader(unittest.TestCase):
    def test_pack_unpack(self):
        num_robots = 5;
        num_balls = 3;

        header = Header(num_robots, num_balls)
        data = header.pack()

        header2 = Header.unpack(data)
        self.assertEquals(num_robots, header2.num_robots)
        self.assertEquals(num_balls, header2.num_balls)

def make_test_detectionframe():
    frame = ssl_detection.SSL_DetectionFrame()
    
    # Add some balls
    ball1 = frame.balls.add()
    ball1.x = 20.5
    ball1.y = 50
    ball1.area = 200
    
    ball2 = frame.balls.add()
    ball2.x = 3.5
    ball2.y = 4.5
    ball2.area = 100
    
    # Add some robots
    robot1 = frame.robots_yellow.add()
    robot1.x = 57
    robot1.y = 23
    robot1.robot_id = 5
    robot1.orientation = math.pi * 0.4
    
    robot2 = frame.robots_blue.add()
    robot2.x = 57
    robot2.y = 23
    robot2.robot_id = 8
    robot2.orientation = math.pi * 0.3

    return frame

class TestFieldInfo(unittest.TestCase):
    def setUp(self):
        self.frame = make_test_detectionframe()
    
    def check_field_info(self, field_info):
        # Check the object counts
        self.assertEquals(2, len(field_info.balls))
        self.assertEquals(2, len(field_info.robots))

        # Check the objects
        for i in xrange(0,len(self.frame.balls)):
            ball1 = field_info.balls[i]
            frame_ball1 = self.frame.balls[i]
            self.assertEqual(frame_ball1.x, ball1.x)
            self.assertEqual(frame_ball1.y, ball1.y)

        frame_robots = []
        frame_robots.extend(self.frame.robots_yellow)
        frame_robots.extend(self.frame.robots_blue)

        for i in xrange(0,len(frame_robots)):
            robot1 = field_info.robots[i]
            frame_robot1 = frame_robots[i]
            self.assertEqual(frame_robot1.x, robot1.pos.x)
            self.assertEqual(frame_robot1.y, robot1.pos.y)
            self.assertEqual(frame_robot1.robot_id, robot1.id)
            self.assertAlmostEqual(frame_robot1.orientation, robot1.heading,2)

    def test_construct(self):
        field_info = FieldInfo(self.frame)
        self.check_field_info(field_info)


    def test_send_data(self):
        fileobj = StringIO.StringIO()

        field_info = FieldInfo(self.frame)
        field_info.send_data(fileobj)

        expected_size = Header.PACKED_SIZE + \
                        Vector2D.PACKED_SIZE * len(self.frame.balls) + \
                        RobotInfo.PACKED_SIZE * len(self.frame.robots_yellow)+\
                        RobotInfo.PACKED_SIZE * len(self.frame.robots_blue)
        
        self.assertEquals(expected_size, len(fileobj.getvalue()))

    def test_pack_unpack(self):
        fileobj = StringIO.StringIO()
                
        field_info = FieldInfo(self.frame)
        field_info.send_data(fileobj)

        field_info2 = FieldInfo.unpack(fileobj.getvalue())
        self.check_field_info(field_info2)



if __name__ == '__main__':
    unittest.main()
