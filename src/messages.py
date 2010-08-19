
# Standard Imports
import struct
import unittest

__doc__ = """
This module defines the basic data structures that are sent over the wire. 
Each one has a pack function which packs its contents into a binary string
which the bluetooth device can read.
"""

# TODO: deal with signed heading floats!!!

# Free helper functions

def pack_float(num):
    """
    Packs floating pointer number to fixed point 0.5 percision value
    that is capped at 254.
    """
    rawNum = int(round(num*2.0))
    if rawNum > 254:
        res = 254
    else:
        res = rawNum
        
    return res

def unpack_float(packedNum):
    """
    Reverse the effects of packing the float
    """
    return packedNum * 0.5    

def pack_int(num):
    """
    Packs the value as a norma int limited to a size of 254
    """
    if num > 254:
        return 254
    return int(round(num))

def unpack_int(num):
    return num

# Classes

class Vector2D(object):
    PACKED_SIZE = 2

    def __init__(self,x,y):
        self.x = x;
        self.y = y;

    def pack(self):
        """Returns the object encoded in a binary string"""
        return struct.pack('BB', pack_float(self.x),  pack_float(self.y))

    @staticmethod
    def unpack(data, unpack_offset = 0):
        """Returns and object build from the packed data"""
        vec = Vector2D(0,0)
        rawX, rawY = struct.unpack_from('BB',data, offset = unpack_offset)
        vec.x = unpack_float(rawX)
        vec.y = unpack_float(rawY)
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
        data = struct.pack('BB', pack_int(self.id), pack_float(self.heading))
        posData = self.pos.pack()
        return data + posData

    @staticmethod
    def unpack(data):
        """Returns and object build from the packed data"""
        rawID, rawHeading = struct.unpack('BB',data[:2])

        robotInfo = RobotInfo(0,0,0)
        robotInfo.id = unpack_int(rawID)
        robotInfo.heading = unpack_float(rawHeading)
        robotInfo.pos = Vector2D.unpack(data, unpack_offset = 2)

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
    def __init__(self, numRobots, numBalls):
        self.numRobots = numRobots
        self.numBalls = numBalls

    def pack(self):
        data = struct.pack('BB',
                           pack_int(self.numRobots),
                           pack_int(self.numBalls))
        return data
    
    @staticmethod
    def unpack(data):
        rawRobotNum, rawBallNum = struct.unpack('BB',data)

        header = Header(0,0)
        header.numRobots = unpack_int(rawRobotNum)
        header.numBalls = unpack_int(rawBallNum)
        return header


# Tests

class TestFunctions(unittest.TestCase):
    def test_pack_float(self):
        self.assertEquals(10, pack_float(5.0))
        self.assertEquals(5, pack_float(2.5))

    def test_unpack_float(self):
        self.assertEquals(7.5, unpack_float(15))

    def test_pack_int(self):
        self.assertEqual(5, pack_int(5))
        self.assertEqual(254, pack_int(255))
        self.assertEqual(254, pack_int(655))

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
        heading = 13.5
        pos = Vector2D(3.5, 6)

        robotInfo = RobotInfo(ID, heading, pos)
        data = robotInfo.pack()

        robotInfo2 = RobotInfo.unpack(data)
        self.assertEquals(ID, robotInfo2.id)
        self.assertEquals(heading, robotInfo2.heading)
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
        numRobots = 5;
        numBalls = 3;

        header = Header(numRobots, numBalls)
        data = header.pack()

        header2 = Header.unpack(data)
        self.assertEquals(numRobots, header2.numRobots)
        self.assertEquals(numBalls, header2.numBalls)


if __name__ == '__main__':
    unittest.main()
