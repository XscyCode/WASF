from logger import logger
from configure import config
import copy

#单一节点数据包
class nodePacket(object):
    def __init__(self, nodeID) -> None:
        self.nodeID = nodeID
        self.timestamp = 0      #当累加到一定程度后会被删除
        self.aggTimestamp = 0   #加入到容器中的时间戳记录
        self.maxLiveTime = config.maxLiveTime  #节点的最大存活时间
        self.jump = 0

    def checkObsolete(self):
        if self.timestamp >= self.maxLiveTime:
            return True
        else:
            return False
    #无效了返回True， 有效返回False
    def timeLapse(self):
        self.timestamp = self.timestamp + 1
        return self.checkObsolete()
    
    def recordJump(self):
        self.jump = self.jump + 1

#数据包类，可以包括多个不同的数据包
class packet(object):
    def __init__(self) -> None:
        self.packets = []
        self.maxNodeCapacity = config.maxQIInFrm  #最多可以包括多少个节点的信息
        self.timestamp = 0

    #时间流逝, 当返回False，表示这个数据包已经超时了。当返回True时，表明这个数据包正常
    def timeLapse(self):
        #更新自己的时间戳
        self.timestamp = self.timestamp + 1
        #更新自己容器里面的包的时间戳
        packetLens = len(self.packets)
        for i in range(packetLens - 1, -1, -1):
            if self.packets[i].timeLapse() == True:
                del self.packets[i]
        return True
    
    def recordJump(self):
        for item in self.packets:
            item.recordJump()

    def getRemainSpace(self):
        return self.maxNodeCapacity - len(self.packets)

    def getCurrentSpace(self):
        return len(self.packets)

    #聚合, 输入参数为一个数据包, 返回的是聚合后的数据包数量
    def aggregation(self, waitAggPackets):
        if self.timestamp > waitAggPackets.timestamp:
            #保留自己的
            for item in waitAggPackets.packets:
                tmp = copy.deepcopy(item)
                tmp.aggTimestamp = self.timestamp
                self.packets.append(tmp)
            return self
        else:
            #保留旧的
            for item in self.packets:
                tmp = copy.deepcopy(item)
                tmp.aggTimestamp = waitAggPackets.timestamp
                waitAggPackets.packets.append(tmp)
            return waitAggPackets

    #聚合，输入参数为一个数据包，返回的是聚合后的数据包，包括两个。
    # 一个是完整的，一个是剩余的。如果不能填满，那么后一个返回值就是None
    def aggregationFull(self, waitAggPackets):
        if self.timestamp > waitAggPackets.timestamp:
            #以自己的作为基本
            for i in range(self.getRemainSpace()):
                if len(waitAggPackets.packets) != 0:
                    #仍然还有等待聚合的
                    tmp = copy.deepcopy(waitAggPackets.packets[0])
                    tmp.aggTimestamp = self.timestamp
                    self.packets.append(tmp)
                    del waitAggPackets.packets[0]
                else:
                    #没有了，直接返回吧
                    return copy.deepcopy(self), None
            #自己已经满了，可以返回了
            return copy.deepcopy(self), waitAggPackets
        else:
            #自己没有来的数据包长远,以对方为基本
            for i in range(waitAggPackets.getRemainSpace()):
                if len(self.packets) != 0:
                    tmp = copy.deepcopy(self.packets[0])
                    tmp.aggTimestamp = waitAggPackets.timestamp
                    waitAggPackets.packets.append(tmp)
                    del self.packets[0]
                else:
                    return copy.deepcopy(waitAggPackets), None
            return copy.deepcopy(waitAggPackets), copy.deepcopy(self)

    def addQI(self, node):
        if self.getRemainSpace() > 0:
            tmp = copy.deepcopy(node)
            # 设置节点的聚合时间戳为当前容器的时间戳
            tmp.aggTimestamp = self.timestamp
            self.packets.append(tmp)
            return True
        else:
            return False