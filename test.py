import unittest

from packet import nodePacket
from packet import packet
from configure import config
import numpy as np

class TestConfigure(unittest.TestCase):
    def test_weight(self):
        a = config.weights
        self.assertEqual(len(a), 4)

#测试基本数据包
class TestNodePacket(unittest.TestCase):
    def test_init(self):
        a = nodePacket(1)
        result = True
        for i in range(10000):
            result = a.timeLapse()
            if result == True:
                self.assertNotEquals(i, 0)
                break
        self.assertTrue(result)

#测试聚合的数据包
class TestPacket(unittest.TestCase):
    def test_remain(self):
        a = packet()
        self.assertGreater(a.getRemainSpace(), 1)


if __name__ == '__main__':
    unittest.main()

