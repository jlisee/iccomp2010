
# Standard Imports
import struct
import unittest
import math

__doc__ = """
This module defines the basic data structures that are sent over the wire. 
Each one has a pack function which packs its contents into a binary string
which the bluetooth device can read.
"""

# TODO: deal with signed heading floats!!!

# Free helper functions

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

# Classes

class Vector2D(object):
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

class RobotInfo(object):
    PACKED_SIZE = 2 + Vector2D.PACKED_SIZE

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
    def unpack(data):
        """Returns and object build from the packed data"""
        raw_data = struct.unpack('B',data[:1])

        robotInfo = RobotInfo(0,0,0)
        robotInfo.id = uncompress_int(raw_data[0])
        robotInfo.heading = unpack_angle(data, unpack_offset = 1)
        robotInfo.pos = Vector2D.unpack(data, unpack_offset = 3)

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
    def __init__(self, num_robots, num_balls):
        self.num_robots = num_robots
        self.num_balls = num_balls

    def pack(self):
        data = struct.pack('BB',
                           compress_int(self.num_robots),
                           compress_int(self.num_balls))
        return data
    
    @staticmethod
    def unpack(data):
        raw_robot_num, raw_ball_num = struct.unpack('BB',data)

        header = Header(0,0)
        header.num_robots = uncompress_int(raw_robot_num)
        header.num_balls = uncompress_int(raw_ball_num)
        return header


# Tests

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

        print 'L',len(data[:1])
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


if __name__ == '__main__':
    unittest.main()
