from asyncore import dispatcher_with_send
from concurrent.futures import thread
import imp
import multiprocessing
from queue import Queue
from neuron import States
import wirelessNode
import neuronNetworks
from configure import config
from multiprocessing import Process
from multiprocessing import Value,Array
import numpy as np
import time
import os

class Model(object):
    def __init__(self):
        self.wn = wirelessNode.wirelessNetwork()
        self.nn = neuronNetworks.neuronNetwork()
        self.wn.setNN(self.nn)
        self.powerlist = [100]*50
        # print(os.getpid(),"test")
        #临时测试一下，将每一个节点都与前一个节点进行连接，看看效果怎么样
        # for i in range(1, config.nodeCount, 1):
        #     #获取所有的连接，比自己小的
        #     tmp = self.wn.linkGroup[i]
        #     for j in tmp:
        #         self.addEdge(i, j)
        #         self.setWeight(i, j, [0.4, 0.6])
        self.complete = True

    def getNodeQI(self):
        myNodeQi = []
        for i in range(1,50,1):
            myNodeQi.append(self.wn.getNodeQI(i))
        return myNodeQi

    def getPower(self):
        return self.powerlist

    def setPower(self,nodepowergroup):
        self.wn.setNodePower(nodepowergroup)

    def setWeight(self, srcID, desID, weight):
        # print("this is flag")
        # print(weight)
        self.nn.setConnectWeight(srcID, desID, weight)
    
    def setLinkGroup(self,linkgroup):
        self.wn.setHistoryLink(linkgroup)
        self.wn.setNN(self.nn)

    def getNodeLink(self,nodeID):
        return self.wn.linkGroup[nodeID]

    def setP(self, t, a, j):
        self.nn.setP(t, a, j)

    def setSelfWeight(self, nodeID, weight):
        self.nn.setNodeSelfWeight(nodeID, weight)
    
    def addEdge(self, srcID, desID):
        self.nn.addConnect(srcID, desID)
    
    def delEdge(self, srcID, desID):
        self.nn.delConnect(srcID, desID)

    def getEdges(self, srcID):
        return self.nn.getEdges(srcID)

    def getNodeState(self, nodeID):
        return self.nn.getNodeState(nodeID)

    def getConnectToNode(self, nodeID):
        return self.nn.getConnectToNode(nodeID)

    def isComplete(self):
        if self.runFlag.value == 0:
            return False
        else:
            return True
    
    def recordStructure(self, stream):
        self.nn.recordStructure(stream)
        self.wn.recordLinkgroup()

    #调用这个函数时，线程会重新跑起来
    def resetResult(self):
        # print(os.getpid(),"kk")
        self.startTest()
    
    def setLastLoss(self, minValue):
        self.nn.setLastLoss(minValue)

    def getResult(self):
        return self.result.value

    def setModelID(self, id):
        self.id = id

    def startTest(self):
        self.runFlag = Value('b', False)
        self.result = Value('f', 1)
        self.powerlist = Array('f',range(self.wn.nodeCount))
        self.t = Process(target=self.doTest, args=(self.nn, self.wn, self.runFlag, self.result, self.powerlist))
        self.t.start()
        return True

    def doTest(self, nn, wn, runFlag, result, powerlist):
        #当未完成时，开始工作，直到完成测试。完成测试后complete会被修改为True
        # start = time.time()
        # print(os.getpid(),"dotest")
        
        timeSec = 0
        powerlistdata = []
        # powerlist.clear()
        slotPerSec = config.slotPerSec
        nn.resetResult()
        # print(os.getpid(),"dotest1")
        while nn.isComplete() == False:
            for i in range(slotPerSec):
                wn.timeLapse(timeSec, i)
            timeSec = timeSec + 1
        runResult = nn.getResult()
        value = np.array(runResult)
        result.value = np.sqrt(((value) ** 2).mean())
        # # print(runResult)
        # value = np.array(runResult) 
        # lossweight = np.array([1,1,1])
        # value = ((value) ** 2) * lossweight
        # # print(np.sum(value))
        # # print(np.sum(lossweight))
        # value = np.sum(value)/np.sum(lossweight)
        # # print(value)
        # value = np.sqrt(value)
        # # print(value)
        # result.value = value
        # print(wn.getNodePower())
        powerlistdata = wn.getNodePower()
        # print(powerlistdata[:])
        for i in range(wn.nodeCount):
          powerlist[i] = powerlistdata[i]
        # print(powerlist[:])
        # if result.value < 0.38 and result.value > 0.378:
        #    result.value = 0.379
        runFlag.value = 1
        # print(time.time() - start)
        