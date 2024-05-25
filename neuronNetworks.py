#这个是管理神经元的，提供了访问接口等等内容。允许外部程序调用
from os import link
from SN import sinkNode
from neuron import States, neuronNode
from enum import Enum
from abc import abstractclassmethod, ABCMeta
from edge import edge
from configure import config
import numpy as np
import random
from logger import logger

#一个权重的评估
class estimatorWeight(object):
    def __init__(self, weight) -> None:
        self.weight = weight            #这两个参数用途是一样的，备用
        self.complete = False          #是否测试完成
        self.testIndex = 0
        self.testCount = config.testCount
        self.testResult = []            #测试结果记录在这里

    #增加一个结果
    def addResult(self, lostValue):
        self.testResult.append(lostValue)
        #logger.logger.info("结果：" + str(lostValue))
        self.testIndex = self.testIndex + 1
        if self.testIndex == self.testCount:
            #完成
            self.complete = True

    #计算均方误差
    def rmse(self,value):
        value = np.array(value)
        return np.sqrt(((value) ** 2).mean())

    #获取评估结果,这里是取均值 
    def getResult(self):
        return self.rmse(self.testResult)

    #检查是否完成
    def getComplete(self):
        return self.complete

    #获取权重索引
    def getWeight(self):
        return self.weight

# #一条边的评估，一条边具有多组不同的权重，都是需要记录的
# class estimatorEdge(object):
#     def __init__(self, sourceID, desID, INN) -> None:
#         self.sourceID = sourceID    #相当与身份标记
#         self.desID = desID
#         self.complete = False       #是否完成标记
#         self.weightGroup = []       #权重组
#         self.INN = INN
#         #产生所有的权重组
#         weights = config.weights
#         for i in range(len(weights)):
#             self.weightGroup.append(estimatorWeight(weights[i]))
#         self.testIndex = 0      #从第0个权重开始测试

#     #激活
#     def active(self):
#         #这条边被激活，需要自己新加这条边。然后设置权重
#         self.INN.addConnect(self.sourceID, self.desID)
#         #logger.logger.debug('增加边线：' + str(self.sourceID) + ' 至 ' + str(self.desID))
#         self.INN.setConnectWeight(self.sourceID, self.desID, self.weightGroup[self.testIndex].getWeight())
#         #logger.logger.debug('修改权重：' + str(self.sourceID) + ' 至 ' + str(self.desID) + ' : ' + str(self.weightGroup[self.testIndex].getWeight()))

#     #增加一个评估结果
#     def addResult(self, lostValue):
#         #找到正在测试的权重，然后把结果给它
#         self.weightGroup[self.testIndex].addResult(lostValue)
#         if self.weightGroup[self.testIndex].getComplete() == True:
#             self.testIndex = self.testIndex + 1
            
#             if self.testIndex == len(self.weightGroup):
#                 self.complete = True
#                 #完成后要删除自己添加的那一条边
#                 self.INN.delConnect(self.sourceID, self.desID)
#                 #logger.logger.debug('删除边线：' + str(self.sourceID) + ' 至 ' + str(self.desID))
#                 return
            
#             #测试完了一组，需要设置新的权重
#             self.INN.setConnectWeight(self.sourceID, self.desID, self.weightGroup[self.testIndex].getWeight())
#             #logger.logger.debug('修改权重：' + str(self.sourceID) + ' 至 ' + str(self.desID) + ' : ' + str(self.weightGroup[self.testIndex].getWeight()))

#     #获得评估结果, 返回最佳的权重组以及对应的值
#     def getResult(self):
#         #统计自己下辖最佳的权重
#         minValue = 1
#         minWeight = None
#         for item in self.weightGroup:
#             value = item.getResult()
#             if value < minValue:
#                 minValue = value
#                 minWeight = item.getWeight()

#         return minWeight, minValue

#     #检查是否完成
#     def getComplete(self):
#         return self.complete
    
#     #获取源节点ID
#     def getSourceID(self):
#         return self.sourceID

#     #获取当前权重索引
#     def getCurWeight(self):
#         return self.weightGroup[self.testIndex].getWeight()
    

# #对多条边的评估，一个节点具有多个不同的边，就是可以有许多的边可以连接到这个节点。
# class estimatorNode(object):
#     def __init__(self, nodeID, INN) -> None:
#         self.nodeID = nodeID        #记录当前是哪个节点了
#         self.edges = []
#         self.complete = False
#         self.INN = INN

#         #散点不能作为目标节点
#         if INN.getNodeState(nodeID) == States.SCATTERED:
#             self.complete = True
#             return

#         #获取到所有的可新建连接的边

#         #先获取到所有的连接到这个节点的节点,指的是神经网络
#         nnConnect = INN.getEdgeToNode(self.nodeID)

#         #得到所有连接到这个节点的实质连接，并去掉ID小于当前节点的
#         wnConnect = INN.getConnectToNode(self.nodeID)
#         if len(wnConnect) == 0:
#             self.complete = True
#             return

#         #查找还没有连接的比自己ID大的节点,有的话，就作为候选
#         for item in wnConnect:
#             if (item not in nnConnect) and (item > self.nodeID):
#                 self.edges.append(estimatorEdge(item, self.nodeID, self.INN))

#         #判定有几个连接
#         if len(self.edges) == 0:
#             self.complete = True
#         else:
#             self.edgeIndex = 0      #存在没有探测的边，设置为0
#             self.edges[self.edgeIndex].active() #激活第一个
    
#     #增加测试结果
#     def addResult(self, lostValue):
#         self.edges[self.edgeIndex].addResult(lostValue)
#         if self.edges[self.edgeIndex].getComplete() == True:
#             self.edgeIndex = self.edgeIndex + 1
#             if self.edgeIndex == len(self.edges):
#                 self.complete = True
#             else:
#                 #还有，就继续激活下一条边
#                 self.edges[self.edgeIndex].active()

#     #获取测试结果, 返回最佳的源节点、权重组
#     def getResult(self):
#         minValue = 1
#         minSrcID = -1
#         minWeight = None
#         for item in self.edges:
#             weight, value = item.getResult()
#             if value < minValue:
#                 minValue = value
#                 minWeight = weight
#                 minSrcID = item.getSourceID()

#         return minSrcID, minWeight, minValue

#     #获取是否完成
#     def getComplete(self):
#         return self.complete

#     #获取节点ID
#     def getNodeID(self):
#         return self.nodeID

#     #返回测试起始节点
#     def getEdge(self):
#         return self.edges[self.edgeIndex].sourceID, self.nodeID
  

# #这个类是进行增加边界工作的
# class addEdgeWorker(object):
#     def __init__(self, INN, lastLoss) -> None:
#         self.INN = INN 
#         self.curAddNode = estimatorNode(0, self.INN)        #增加到哪个节点了, 默认是SN
#         self.INN = INN                                      #它是神经网络的接口
#         self.lastLoss = lastLoss                       #上一次结果,如果没有比这个还低，那么并不需要对网络进行任何的变动

#         self.complete = False
#         #检查是否可以
#         if self.curAddNode.getComplete() == True:   #SN节点直接就满了
#             #直接寻找下一个节点
#             if self.getNextNode() == False:
#                 self.complete = True
#         else:   #没事了，直接开始吧
#             pass

#     #在失去后续的情况下，获取下一个可测试的节点,这是一个递归函数
#     def getNextNode(self):
#         #得到所有连接到这个节点的实质连接
#         temp = self.INN.getConnectToNode(self.curAddNode.nodeID)
#         wnConnect = []
#         for item in temp:
#             if item > self.curAddNode.nodeID:
#                 wnConnect.append(item)

#         if len(wnConnect) == 0:
#             self.complete = True
#             #logger.logger.debug('已经到达尾部节点')
#             return False   #到头了

#         #没有到头，那就随机的找一个
#         randomValue = random.randint(0,len(wnConnect) - 1)

#         #logger.logger.debug('延长至节点' + str(wnConnect[randomValue]))
#         self.curAddNode = estimatorNode(wnConnect[randomValue], self.INN)
#         #判断节点是否完成或者是否是一个散点，是的话都不具备作为候选的可能
#         if self.curAddNode.getComplete() == True or self.INN.getNodeState(self.curAddNode.nodeID) == States.SCATTERED:
#             return self.getNextNode()
#         else:
#             return True

#     #获取上次结果的转换值
#     def getLastLoss(self):
#         value = np.array(self.lastLoss)
#         return np.sqrt(((value) ** 2).mean()) 

#     #获取当前测试的节点ID
#     def getTestEdge(self):
#         return self.curAddNode.getEdge()

#     #完成了增加边界任务，返回True。 未完成就返回False
#     def addResult(self, lossValue):

#         #得到一次结果,注意这个结果是SN的上一个结果。
#         self.curAddNode.addResult(lossValue)

#         #检查当前节点是否已经完成了工作
#         if self.curAddNode.getComplete() == True:
#             #获取最佳的结构，并更新到实际的网络中
#             opSrcID, opWeight, opValue = self.curAddNode.getResult()
#             if opValue < self.getLastLoss():
#                 logger.logger.info('节点测试完成，新增连接从' + str(opSrcID) + ' 到 ' + str(self.curAddNode.nodeID) + '. 权重为 ' + str(opWeight))
#                 logger.logger.info('原有损失值为 ' + str(self.lastLoss) + ' 新损失值为 ' + str(opValue))
#                 self.lastLoss = opValue
                
#                 self.INN.addConnect(opSrcID, self.curAddNode.nodeID)
#                 self.INN.setConnectWeight(opSrcID, self.curAddNode.nodeID, opWeight)

#                 self.curAddNode = estimatorNode(opSrcID, self.INN)

#                 #如果选择的节点已经没有添加边线的可能了，那么继续寻找下一个节点
#                 if self.curAddNode.complete == True:
#                     if self.getNextNode() == False:
#                         self.complete = True  
#             else:
#                 #没有得到最低的，继续延伸
#                 if self.getNextNode() == False:
#                     self.complete = True 


# #删除的边的情况
# class delEdgeRecord(object):
#     def __init__(self, fromID, toID, weight, lossValue) -> None:
#         self.fromID = fromID
#         self.toID = toID
#         self.weight = weight
#         self.beforeLossValue = lossValue
#         self.results = []
#         self.testCount = config.testCount
#         self.complete = False
#         self.canDelete = False

#     #当某一个边线被删除并且结果更好时，需要更新这个值
#     def updateBeforeLossValue(self, lossValue):
#         self.beforeLossValue = lossValue

#     def rmse(value):
#         return np.sqrt(((value) ** 2).mean())

#     def addResult(self, lossValue):
#         self.results.append(lossValue)
#         self.testCount = self.testCount - 1
#         if self.testCount == 0:
#             self.complete = True
#             #计算能够删除
#             curResult = self.rmse(self.results)
#             if curResult < self.beforeLossValue:
#                 self.canDelete = True

#     def getResult(self):
#         return self.rmse(self.results)

 
# class delEdgeNode(object):
#     def __init__(self, nodeID, INN, curLossValue) -> None:
#         self.nodeID = nodeID    #被删除的边线起点节点
#         self.edges = []         #等待测试的边线列表
#         self.INN = INN
#         self.lastLossValue = curLossValue
#         self.complete = False
#         #获取所有可以测试的列表
#         nnConnect = self.INN.getEdgesFromThis(self.nodeID)
#         for item in nnConnect:
#             self.edges.append(delEdgeRecord(self.nodeID, item, self.INN.getWeight(self.nodeID, item), curLossValue))

#         #没有可用的边线直接完成就可以
#         if len(self.edges) == 0:
#             self.complete = True

#         #从第一个边线开始测试
#         self.index = 0

#     #激活测试
#     def active(self):
#         #删除边线，然后开始评估
#         self.INN.delEdge(self.edges[self.index].fromID, self.edges[self.index].toID)
    
#     #增加一个结果
#     def addResult(self, lossValue):
#         self.edges[self.index].addResult(lossValue)
#         if self.edges[self.index].complete == True:
#             #已经完成了测试
#             if self.edges[self.index].canDelete == False:
#                 #效果不好，需要恢复边线
#                 self.INN.addEdge(self.edges[self.index].fromID, self.edges[self.index].toID)
#                 self.INN.setConnectWeight(self.edges[self.index].fromID, self.edges[self.index].toID, self.edges[self.index].weight)
#             else:
#                 #效果挺好，那么保留这个删除,并更新当前最低的损失
#                 self.lastLossValue = self.edges[self.index].getResult()
#                 for item in self.edges:
#                     item.updateBeforeLossValue(self.lastLossValue)
            
#             #最后加1
#             self.index = self.index + 1
#             if self.index == len(self.edges):
#                 self.complete = True
#             else:
#                 #激活下一次测试
#                 self.active()


# #删除节点连线
# class delEdgeWorker(object):
#     def __init__(self, INN, lossValue) -> None:
#         self.INN = INN
#         self.complete = False
#         #定位到末尾节点
#         nodeCount = config.nodeCount
#         self.lastLossValue = lossValue
#         self.curNode = delEdgeNode(nodeCount - 1, INN, self.lastLossValue)
#         if self.curNode.complete == True:
#             self.getNext(self.curNode.nodeID)

#     #获取下一个可以作为边线的源头的节点
#     def getNext(self, curNodeID):
#         #随机找前面的节点,直接获取无线连接即可，无线连接是无方向的。
#         wwConnect = self.INN.getConnectToNode(curNodeID)
#         candidate = []
#         for item in wwConnect:
#             if item < curNodeID:
#                 candidate.append(item)
#         if len(candidate) == 0:
#             self.complete = True
#             return
#         #随机选择一个节点
#         nextNodeID = candidate[random.randint(0, len(candidate - 1))]
#         if len(self.INN.getEdgeFromNode(nextNodeID)) == 0:
#             #这个节点没有可以删除的边线
#             self.getNext(nextNodeID)
#         else:
#             self.curNode = delEdgeNode(nextNodeID, self.INN, self.lastLossValue)

#     #增加一个结果
#     def addResult(self, value):
#         self.curNode.addResult(value)
#         if self.curNode.complete == True:
#             self.getNext()

# #用于调整权重节点的结果记录
# class adjstWeightResult(object):
#     def __init__(self, weight) -> None:
#         self.weight = weight
#         self.complete = False
#         self.testIndex = 0
#         self.testCount = config.testCount
#         self.testResult = []            #测试结果记录在这里

#     def addResult(self, lostValue):
#         self.testResult.append(lostValue)
#         #logger.logger.debug("结果：" + str(lostValue))
#         self.testIndex = self.testIndex + 1
#         if self.testIndex == self.testCount:
#             #完成
#             self.complete = True

#     #计算均方误差
#     def rmse(self,value):
#         value = np.array(value)
#         return np.sqrt(((value) ** 2).mean())

#     #获取评估结果,这里是取均值 
#     def getResult(self):
#         return self.rmse(self.testResult)

#     #检查是否完成
#     def getComplete(self):
#         return self.complete

#     #获取权重索引
#     def getWeight(self):
#         return self.weight

# #用于调整节点的权重
# class adjustWeight(object):
#     def __init__(self, lastResult, inn) -> None:
#         self.inn = inn
#         self.lastResult = lastResult
#         self.testNode = random.randint(1, config.nodeCount - 1)
#         self.lastNodeWeight = inn.getNodeSelfWeight(self.testNode)
#         self.complete = False
#         self.weights = []
#         self.weightsIndex = 0
#         for weight in config.weights:
#             self.weights.append(adjstWeightResult(weight))

#     def addResult(self, lossValue):
#         if self.complete != True:
#             self.weights[self.weightsIndex].addResult(lossValue)
#             #检查本次结果是否完成，完成就继续下一个
#             if self.weights[self.weightsIndex].complete == True:
#                 #增加索引，如果过大就本次完成
#                 self.weightsIndex = self.weightsIndex + 1
#                 if self.weightsIndex >= len(self.weights):
#                     self.complete = True
#                     self.doAfterAdjust()
#                 else:
#                     #切换到下一个权重
#                     self.inn.setNodeSelfWeight(self.testNode, self.weights[self.weightsIndex].weight)
#             else:
#                 pass
#             #如果没有完成，那么什么也不做，继续往下走就可以了。
            
#     #当完成后，开始调整节点的权重
#     def doAfterAdjust(self):
#         #检查是否有比当前的效果更好的，如果有，那么就处理一下。
#         index = -1
#         minValue = self.lastResult
#         for i in range(len(self.weights)):
#             if self.weights[i].getResult() < minValue:
#                 minValue = self.weights[i].getResult()
#                 index = i
#         if index != -1:
#             #到这里就是有一个更好的结果了
#             self.inn.setNodeSelfWeight(self.testNode, self.weights[index].weight)
#             self.lastResult = minValue
#         else:
#             #没有更好的结果了。将其调整为之前的那个。
#             self.inn.setNodeSelfWeight(self.testNode, self.lastNodeWeight)

#     #获取增加状态
#     def getState(self):
#         return self.testNode, self.weights[self.weightsIndex].weight


class WorkState(Enum):
    ON_ADD_EDGE = 1
    ON_DEL_EDGE = 2
    ON_ADJUST_WEIGHT = 3
    ON_WAIT_TO_ADD = 4
    ON_WAIT_TO_DEL = 5
    ON_WAIT_TO_ADJUST = 6
    ON_STABLE = 7


#神经网络对内接口
class INN():
    #获取有哪些节点连接到这个节点
    def getEdgeToNode(self, targetNodeID):pass

    def getEdgeFromNode(self, srcID): pass

    def getConnectToNode(self, targetNodeID):pass

    def setConnectWeight(self, srcID, desID, weight): pass

    def delConnect(self, srcID, desID): pass

    def addConnect(self, srcID, desID): pass

    def getConnectWeight(self, srcID, desID): pass

    def getNodeSelfWeight(self, nodeID): pass

    def setNodeSelfWeight(self, nodeID, weight): pass

#神经网络对外接口
class INeuronNetworks():
    def timeLapse(self, nodeID, timeOffset, inputVector=None): pass

    def setLinkGroup(self, linkGroup): pass

    def overTransmit(self, packet): pass

    def getNodeState(self, desID): pass

class neuronNetwork(INN, INeuronNetworks):
    #maxInfroInSingleFrm 是单帧最大值，根据使用的协议以及压缩算法确定
    def __init__(self) -> None:
        nodeCount = config.nodeCount - 1    #需要减去SN的占位
        self.SN = sinkNode(0)

        self.nodes = []                     #拥有的神经元节点，  注意：不是所有的神经元都加入到网络中并发挥了作用
        self.nodes.append(self.SN)          #占位，省的错乱

        self.linkGroup = None

        self.addEdgeWorker = None
        self.delEdgeWorker = None
        self.adjustWorker = None

        self.state = WorkState.ON_WAIT_TO_ADD  #等待的状态

        #产生神经元
        for i in range(nodeCount):
            item = neuronNode(i + 1)
            #按照顺序添加
            self.nodes.append(item)

    #设置最小值
    def setLastLoss(self, minValue):
        self.SN.setLastLoss(minValue)
    
    def setP(self, t, a, j):
        self.SN.setP(t, a, j)

    #设置连接
    def setLinkGroup(self, linkGroup):
        self.linkGroup = linkGroup

    #获取节点状态
    def getNodeState(self, desID):
        return self.nodes[desID].state

    def getNodeSelfWeight(self, nodeID):
        return self.nodes[nodeID].selfWeight
    
    def setNodeSelfWeight(self, nodeID, weight):
        self.nodes[nodeID].selfWeight = weight

    def isComplete(self):
        return self.SN.isComplete()

    def resetResult(self):
        self.SN.resetResult()

    def getResult(self):
        return self.SN.getResult()


    #调用节点的时间流逝
    def timeLapse(self, nodeID, timeOffset, inputVector = None):
        if nodeID == 0:
            #SN
            result = self.SN.timeLapse(timeOffset)
        else:
            result = self.nodes[nodeID].timeLapse(inputVector)
        return result

    def overTransmit(self, packet):
        self.SN.recvPacket(packet)
    
    #获取上一轮的状态，在SN的日常任务后，如果不为None，可以获取到
    def getSNStates(self):
        return self.SN.getLastStates()

    #获取当前稳定情况下的损失值
    def getCurStableLoss(self):
        if self.state == WorkState.ON_ADD_EDGE:
            return self.addEdgeWorker.getLastLoss()
        elif self.state == WorkState.ON_ADJUST_WEIGHT:
            return self.adjustWorker.lastResult
        else:
            return 1
    
    #INN接口的部分

    #获取到某个节点的边线
    def getEdgeToNode(self, targetNodeID):
        #查找所有连接到这个节点的连接
        result = []
        for item in self.nodes:
            if item.nodeID == targetNodeID:
                continue
            if item.connectToSomeNode(targetNodeID) == True:
                result.append(item.nodeID)
        return result

    #获取边线
    def getEdges(self, srcID):
        return self.nodes[srcID].getEdges()

    #获取某个节点连接到的其他节点，神经网络中
    def getEdgeFromNode(self, srcID):
        return self.nodes[srcID].getEdgesFromThis()

    #获取节点的连接关系
    def getConnectToNode(self, targetNodeID):
        return self.linkGroup[targetNodeID]


    #修改边的权重
    def setConnectWeight(self, srcID, desID, weight):
        node = self.nodes[srcID]
        node.setEdgeWeight(srcID, desID, weight)

    #获取边的权重
    def getConnectWeight(self, srcID, desID):
        return self.nodes[srcID].getWeight(srcID, desID)

    #删除边
    def delConnect(self, srcID, desID):
        node = self.nodes[srcID]
        node.delEdge(desID)

    #增加边
    def addConnect(self, srcID, desID):
        node = self.nodes[srcID]
        node.addEdge(desID)

    #记录结构
    def recordStructure(self, stream):
        for node in self.nodes:
            node.recordStructure(stream)
    
    
