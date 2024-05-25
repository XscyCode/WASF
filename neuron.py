#这个文件是神经元的类
import random
from edge import edge
import numpy as np
from configure import config

from enum import Enum

class States(Enum):
    SCATTERED = 1
    CONNECTED = 2

#神经网络节点类： 注意，不是无线节点类，虽然它们之间有关系，但将其抽象为两个不同的类，因为它们处于不同的层级
class neuronNode(object):
    def __init__(self, id) -> None:
        self.nodeID = id
        self.edges = []         #与其他节点的连接记录, 里面的内容是连接的节点
        self.state = States.SCATTERED   #初始化时都是散点状态
        self.selfWeight = [0.2,0.2,0.2]   #所有节点的初始化的给自己的权重
        #self.selfWeight = config.getWeightNodeInit()
        self.maxLiveTime = config.getMaxLiveTime()
        self.maxAgg = config.getMaxQIInFrm()

    #增加一条边
    def addEdge(self, des, weight = None):
        newEdge = edge(self.nodeID, des)
        #print(weight)
        if weight != None:
            newEdge.setWeight(weight)
        #添加并修改状态
        self.edges.append(newEdge)
        if newEdge.fromID == 0 and newEdge.toID == 0:
            pass
        self.state = States.CONNECTED

    #删除一条边
    def delEdge(self, desID):
        for item in self.edges:
            if item.toID == desID:
                #删除这条边
                self.edges.remove(item)
                #如果节点已经没有任何的边了，那么就修改成散点
                if len(self.edges) == 0:
                    self.state = States.SCATTERED
                return True
        return False

    #是否连接到某个节点
    def connectToSomeNode(self, nodeID):
        for item in self.edges:
            if item.toID == nodeID:
                return True
        return False

    #修改某一条边的权重
    def setEdgeWeight(self, srcID, desID, weight):
        if srcID != self.nodeID:
            return False
        for item in self.edges:
            if item.toID == desID:
                item.setWeight(weight)
                return True
        print("Cannot find the edge!\n")
        return False    #未找到
    # 获取自身权重
    def getNodeWeight(self):
        return self.selfWeight


    #获取某一条边的权重
    def getEdgeWeight(self, srcID, desID):
        if srcID != self.nodeID:
            return None
        
        for item in self.edges:
            if item.toID == desID:
                return item.getWeight()
        return None

    #获取所有的边
    def getEdges(self):
        return self.edges

    #获取所有连接到的节点
    def getEdgesFromThis(self):
        result = []
        for item in self.edges:
            result.append(item.toID)
        return result

    #提取对应的输入数据
    def getInputVector(self, inputVector,fromID, toID):
        #inputVector是字典格式
        result = []
        result.append(inputVector[str(fromID)])
        result.append(inputVector[str(toID)])
        result.append(inputVector['timeOffset'])
        return result

    #每过一段时间时，就会触发,它的输入参数是节点数据包，里面包括了两个值，
    # 分别是数据包的时间以及数据包的聚合数量
    def timeLapse(self, inputVector): 
        if self.state == States.SCATTERED:
            #散点不需要有什么动作
            return None

        #下面这里就是激活函数，需要通过计算做出决断往哪转发。
        #做法是通过各候选转发节点的权重与当前数据量计算得到结果
        #然后取概率最高者进行转发。

        #先计算给自己的，也就是等待不转发的概率
        #首先获取自身数据量
        toSelfInputVector = self.getInputVector(inputVector,self.nodeID,self.nodeID)
        toSelf = np.sum(np.multiply(toSelfInputVector, self.selfWeight))
        connectID = None
        
        for item in self.edges:
            result = item.calc(self.getInputVector(inputVector, self.nodeID, item.toID))
            if result > toSelf:
                toSelf = result
                connectID = item.toID
        #这里的激活函数的中间计算过程，只有一个1，其他都是0. 为0不用处理，为1就是需要处理的
        #计算的最后一步交由上层的仿真部分进行处理
        return connectID

    #记录结构
    def recordStructure(self, stream):
        for item in self.edges:
            itemRecord = 'edge:'
            weight = item.getWeight()
            itemRecord = itemRecord + str(item.fromID) + ':' + str(item.toID) + ':'
            for i in weight:
                itemRecord = itemRecord + str(i) + ':'
            itemRecord = itemRecord[0:len(itemRecord) - 1]
            stream.write(itemRecord + '\n')
        #记录自己的权重
        itemRecord = 'selfWeight:' + str(self.nodeID) + ":"
        for item in self.selfWeight:
            itemRecord = itemRecord + str(item) + ':'
        itemRecord = itemRecord[0:len(itemRecord) - 1]
        stream.write(itemRecord + '\n')


