#这个文件是描述无线节点的

from configure import config
from abc import abstractclassmethod, ABCMeta
import random
from packet import packet
from packet import nodePacket
from neuron import States
import copy
from logger import logger
import time
import os
import numpy as np
class node(object):
    def __init__(self, nodeID, linkGroup,power, iwn) -> None:
        self.nodeID = nodeID
        self.linkGroup = linkGroup
        self.dataGeneralCycle = config.dataGeneralCycle     #多少秒产生数据
        self.slotPerSecond = config.slotPerSec              #每秒多少个时间槽

        self.packet = None       #节点当前的数据包，一般是一个，多的认为直接通过地理路由方法送到了SN，这里只关注未被聚合的信息
        
        self.power = power
        # if(self.nodeID == 7):print(os.getpid(),self.nodeID)
        self.iwn = iwn

        #设置数据产生时间
        self.createDataTimeSec = random.randint(0, self.dataGeneralCycle - 1)
        self.createDataTimeSlot = random.randint(0, self.slotPerSecond - 1)

    # 电量消耗模型，100/0.01=10000份
    def powerConsumption(self,n):
        self.power = self.power-(np.log(n+1)/np.log(8)* 0.001)
        # print("pp:"+str(self.power))
    
    # 获取电量    
    def getPower(self):
        # print(self.power)
        return self.power

    # 设置电量    
    def setPower(self,power):
        # print(self.power)
        self.power = power

    #检查满了的数据包

    def checkFull(self):
        if self.packet.getRemainSpace() == 0:
            #直接发送给SN，认为传输完成了
            self.neuronNetwork.overTransmit(self.packet)
            self.packet = None
            return True
        else:
            return False

    #产生数据
    def createData(self):
        #因为只有不全的packet，所以需要合并
        if self.nodeID == 0:
            return

        if self.packet == None:
            #产生一个新的packet
            self.packet = packet()
        
        #packets里面有数据包的存在，那么将自己的数据存放进去
        #先产生一个自己的数据吧
        newData = nodePacket(self.nodeID)
        self.packet.addQI(newData)

        #检查是否满了
        if self.packet.getRemainSpace() == 0:
            self.neuronNetwork.overTransmit(self.packet)
            self.packet = None

    #在散点时，将数据包发送给最近的非散点
    def sendDataToConnected(self):
        for item in self.linkGroup[self.nodeID]:
            if self.iwn.getNodeState(item) == States.CONNECTED:
                #logger.logger.info('散点发送数据包: ' + str(self.nodeID) + ' -> ' + str(item))
                self.iwn.sendDataToNode(item, self.packet)
                self.packet = None
                return
        #如果附近真的没有，那么直接清空缓存吧
        self.packet = None

    # 获取周边节点信息，生成输入值
    def getInputVector(self, timeOffset):
        #生成一个字典
        result = {'timeOffset': timeOffset}
        if self.packet == None:
            result[str(self.nodeID)] = 0
        else:
            result[str(self.nodeID)] = self.packet.getRemainSpace()

        for item in self.linkGroup[self.nodeID]:
            result[str(item)] = self.iwn.getNodeQI(item)
        return result

    #时间流逝函数，仿真时间走动，节点会消耗能量，发送数据。
    def timeLapse(self, timeSec, timeOffset):
        # if(self.nodeID == 7): 
        #     print(self.power)
        #     print(self.linkGroup[self.nodeID])
        #检查是否需要产生数据
        if (timeSec % self.dataGeneralCycle) == self.createDataTimeSec and timeOffset == self.createDataTimeSlot:
            self.createData()
            # self.powerConsumption(1)   # 产生数据消耗1份电量
        
        #做出决策，如果是散点，那么传输数据就完事了。如果不是散点，那么需要整理数据并给神经网络做出决策
        if self.iwn.getNodeState(self.nodeID) == States.SCATTERED:
            #散点
            if (self.packet != None):
                # 发送数据根据当前数据量消耗电量,先消耗电量，再发送，否则数据就没了
                self.powerConsumption(self.packet.getCurrentSpace())
                # 记录跳数
                self.packet.recordJump()
                #查找最近的非散点，把数据给他
                self.sendDataToConnected()
                
                 
        else:
            #对自己的数据包内的时间戳进行变动
            if (self.packet != None):
                self.packet.timeLapse()
                #因为系统是从前向后扫描，数据是从后向前传递，所以不会出现一个数据包在一个时间槽内被增加了两次的情况
                #本节点是神经网络的连接节点，需要做出神经网络决策的
                result = self.neuronNetwork.timeLapse(self.nodeID, timeOffset, self.getInputVector(timeOffset))
                if result != None and result != self.nodeID:
                    #需要转发数据，如果是自己，那么忽略就可以
                    self.packet.recordJump()
                    # 发送数据根据当前数据量消耗电量
                    self.powerConsumption(self.packet.getCurrentSpace())
                    self.iwn.sendDataToNode(result, self.packet)
                    self.packet = None
            
            if self.nodeID == 0:
                self.neuronNetwork.timeLapse(self.nodeID, timeOffset)
    #设置NN
    def setNeuronNetwork(self, nn):
        self.neuronNetwork = nn
    def setHistoryLinkGroup(self,linkgroup):
        self.linkGroup = linkgroup

    #接收到其他节点的信息
    def recvData(self, packet):
        #这是很重要的一部分，完成之后，就可以进行测试了.
        #如果是SN节点，那么直接给SN节点就可以了
        
        if self.nodeID == 0:
            self.neuronNetwork.overTransmit(packet)
        else:
            # self.powerConsumption(2)   # 接受数据消耗2份电量
            tmp = copy.deepcopy(packet)
            tmp.waitTime = 0
            if self.packet == None:
                #本身没有数据，那么直接用就可以
                self.packet = tmp
            else:
                #进行合并
                if self.packet.getRemainSpace() > len(tmp.packets):
                    #并没有填满，那么直接聚合就可以
                    self.packet = copy.deepcopy(self.packet.aggregation(tmp))
                    #完成聚合了，那么这个tmp就没有什么用途了
                    if self.packet.getRemainSpace() == 0:
                        self.neuronNetwork.overTransmit(self.packet)
                        self.packet = None
                else:
                    #一个数据包不够，那么只能先填满一个，然后将另一个作为自己的数据包
                    tmp, self.packet = self.packet.aggregationFull(tmp)
                    self.neuronNetwork.overTransmit(tmp)
                    

    #获取信息量
    def getQI(self):
        if self.nodeID == 0:
            return config.maxQIInFrm
        else:
            if self.packet == None:
                return 0
            else:
                # print(len(self.packet.packets))
                return len(self.packet.packets)

        

class IWN():
    
    def sendDataToNode(self, desID, packet): 
        pass

    def getNodeState(self, desID): 
        pass

    def getNodeQI(self, desID): 
        pass
    
    def getNodePower(self, desID):
        pass

class wirelessNetwork(IWN):
    def __init__(self) -> None:
        super().__init__()
        #开始建立网络
        self.nodes = []
        self.nodeCount = config.nodeCount
        self.linkGroup = []
        self.PowerGroup = [100]*self.nodeCount
        self.generateLink()
        
        #产生节点,注意的是节点0是SN。这里就不区分对待了，节点自己区分吧
        for i in range(self.nodeCount):
            self.nodes.append(node(i, self.linkGroup, self.PowerGroup[i],self))


    def setNN(self, neuronNetwork):
        self.neuronNetwork = neuronNetwork
        self.neuronNetwork.setLinkGroup(self.linkGroup)
        #设置NN
        for item in self.nodes:
            item.setNeuronNetwork(neuronNetwork)

    #实现一下接口
    def sendDataToNode(self, desID, packet):
        self.nodes[desID].recvData(packet)

    #获取节点状态
    def getNodeState(self, desID):
        return self.neuronNetwork.getNodeState(desID)

    #获取节点信息量
    def getNodeQI(self, desID):
        return self.nodes[desID].getQI()
    
    # 获取当前网络中所有节点电量
    def getNodePower(self):
        for i in range(self.nodeCount):
            self.PowerGroup[i] = self.nodes[i].getPower()
        # print(self.PowerGroup[:])
        return self.PowerGroup

    # 设置当前网络中所有节点电量
    def setNodePower(self,powerGroup):
        for i in range(self.nodeCount):
           self.nodes[i].setPower(powerGroup[i])

    #产生连接
    def generateLink(self):
        #先产生所需的节点连接空间
        #需要注意的是节点的连接是双向的,这里就简单粗暴的相等了
        connectRangeMin = config.connectRangeMin
        connectRangeMax = config.connectRangeMax
        # print(os.getpid(),"logtest")
        #遍历所有的节点，为它们添加连接，需要注意的是，这可能会出现不对称的问题。所以需要先对节点赋值，然后检测，再建立起连接
        for i in range(self.nodeCount):

            # rangeValue = random.randint(connectRangeMin, connectRangeMax)
            rangeValue = 4

            #然后按照范围进行添加，添加后是单向的，之后再检查，删除单向的
            connects = []
            for j in range(i - rangeValue, i + rangeValue + 1, 1):
                if j >= 0 and j < config.nodeCount and i != j:
                    connects.append(j)
            self.linkGroup.append(connects)
        
        #这就获得了所有单向的连接，然后将删除不能双向奔赴的
        for i in range(self.nodeCount):
            for j in range(len(self.linkGroup[i]) - 1, -1, -1):
                if i in self.linkGroup[self.linkGroup[i][j]]:
                    #有，那就不用动了
                    pass
                else:
                    del self.linkGroup[i][j]
        # print(self.linkGroup[1])
        return
    
    #修改节点连接，目前仅支持整体修改，为了可以读取历史运行结果
    def setHistoryLink(self,historyListGroup):
        #清空原链接
        self.linkGroup.clear()
        #获取历史链接
        self.linkGroup = historyListGroup
        #给每一个节点都更改信息
        for i in range(self.nodeCount):
            self.nodes[i].setHistoryLinkGroup(historyListGroup)
        

    #接受时间流逝
    def timeLapse(self, timeSec, timeOffset):
        for i in range(len(self.nodes)):
            self.nodes[i].timeLapse(timeSec, timeOffset)
        
    def recordLinkgroup(self):
        stream = open('historyLink.txt', 'a+')
        stream.write('******************************************************\n')
        stream.write('this is the current NodeLinkGroup\t')
        stream.write(time.strftime('%m-%d %H:%M:%S'))
        stream.write('\n******************************************************\n')
        stream.write(str(self.linkGroup))
        stream.write('\n') 
        stream.flush()
        stream.close()