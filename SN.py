#神经网络出口，神经元可以建立与出口的连接。出口有自己的运行逻辑以区别与普通的神经元节点。
from unittest import result
from neuron import States
import packet
from configure import config
import copy
import neuron
from logger import logger
import numpy as np
import math


class sinkNode(neuron.neuronNode):
    def __init__(self, id) -> None:
        self.id = 0     # 默认SN就是ID为0的节点
        self.nodeID = 0
        self.nodeCount = config.nodeCount - 1     #除了SN之外的节点数量
        self.maxInforInSingleFrm = config.maxQIInFrm
        self.cycleWidth = config.maxLiveTime
        self.recvs = []                 #存储本轮内收到的数据包
        self.dataCreateCycle = config.dataGeneralCycle
        self.slotPerSec = config.slotPerSec

        self.lastLoopRecvs = []         #上一轮收到的数据包
        self.lastLossValue = 1

        self.timeOffset = 0
        self.timeSec = 0
        self.edges = []
        self.state = States.CONNECTED

        self.result = []
        self.testCount = config.testCount
         
        self.minlossValue = 1
        self.jumpmax = 30
        #初始化各损失来源在总体损失度函数中的权重比例调整因子
        self.timeLossPropAdjFactor = 1
        self.aggLossPropAdjFactor = 1
        self.jumpLossPropAdjFactor = 1

    def setP(self, timeLoss=1, aggLoss=1, jumpLoss=1):
      self.timeLossPropAdjFactor = timeLoss
      self.aggLossPropAdjFactor = aggLoss
      self.jumpLossPropAdjFactor = jumpLoss

    def recvPacket(self, packet):
        #SN节点的数据包，已经完成了传输，不再进行时间流逝
        self.recvs.append(copy.deepcopy(packet))
    
    def isComplete(self):
        if len(self.result) >= self.testCount:
            return True
        else:
            return False
    
    def resetResult(self):
        self.result.clear()

    #计算均方误差
    def rmse(self,value):
        value = np.array(value)
        return np.sqrt(((value) ** 2).mean())
        # print(value)
        # value = np.array(value)
        # print(value)
        # value = np.sqrt((value**2).mean())
        # print('hh'+str(value))
        # lossweight = np.array([1,1,1])
        # value = ((value) ** 2) * lossweight
        # value = np.sum(value)/np.sum(lossweight)
        # value = np.sqrt(value)
        # return value

    def setLastLoss(self, minlossValue):
        self.minlossValue = minlossValue

    def getResult(self):
        self.result.sort()
        return self.result[0:-1]

    def getValue(self):
        self.result.sort()
        return self.rmse(self.result[0:-1])

    #不断的调用这个函数，SN需要自己在何时的时候计算损失值
    #更新了一轮，则返回损失值，否则返回None
    def timeLapse(self, timeOffset):
        self.timeOffset = timeOffset
        if timeOffset == self.slotPerSec - 1:
            self.timeSec = self.timeSec + 1
            if self.timeSec % self.dataCreateCycle == 0:
                #已经到了最新的一节了，计算上一次的情况
                lost,lossNode = self.calcLost()
                self.lastLossValue = lost
                self.result.append(lost)

                self.lastLoopRecvs.clear()
                #检查，如果达到了历史最佳，那么需要记录一下聚合的数据是什么样子的
                # if len(self.result) >= 3 and self.rmse(self.result) < self.minlossValue:
                #     logger.logger.info('--------------------------------------')
                #     logger.logger.info('当前损失值:{}, 当前最小损失值{}'.format(self.rmse(lost), self.minlossValue)) 
                #     self.minlossValue = self.rmse(lost)
                    
                #     for item in self.recvs:
                #         self.lastLoopRecvs.append(item)
                #         recvListID = ''
                #         for xxx in item.packets:
                #             recvListID = recvListID + str(xxx.nodeID) + ','
                #         logger.logger.info('SN 接收到的数据包列表 ' + recvListID)    
                    
                #     logger.logger.info('**********************************************')    

                if len(self.result) >= 4:              
                    if self.getValue() < self.minlossValue + 0.1:      
                        logger.logger.info('--------------------------------------')
                        logger.logger.info('当前损失值:{}, 当前损失向量:{}'.format(self.rmse(lost), lost)) 
                        logger.logger.info('当前最小损失值{}，当前损失方差:{}'.format(self.minlossValue, self.getValue())) 
                        logger.logger.info('当前丢失节点数 {} '.format(lossNode))           
                        for item in self.recvs:
                            self.lastLoopRecvs.append(item)
                            recvListID = ''
                            for xxx in item.packets:
                                recvListID = recvListID + str(xxx.nodeID) + ':' + str(xxx.timestamp) + ":" + str(xxx.jump) + ', '
                            logger.logger.info('SN 接收到的数据包列表 ' + recvListID)    
                        
                        logger.logger.info('**********************************************')   
                # if lost[0] < 0.13 and lost[1] < 0.13 and lost[2] < 0.13:
                #     logger.logger.info('--------------------------------------')
                #     logger.logger.info('本次损失值:{}, 当前损失向量:{}, 当前最小损失值{}'.format(self.rmse(lost), lost, self.minlossValue))           
                #     for item in self.recvs:
                #         recvListID = ''
                #         for xxx in item.packets:
                #             recvListID = recvListID + str(xxx.nodeID) + ':' + str(xxx.timestamp) + ":" + str(xxx.jump) + ', '
                #         logger.logger.info('SN 接收到的数据包列表 ' + recvListID)    
                        
                #     logger.logger.info('****xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx***')   
  

                #清理现有的记录
                self.recvs.clear()
                return lost
            else:
                return None
        else:
            return None
        
    #删除重复的数据包
    def refinePacket(self):
        recvList = []
        for packet in self.recvs:
            for i in range(len(packet.packets) - 1, -1, -1):
                if packet.packets[i].nodeID not in recvList:
                    recvList.append(packet.packets[i].nodeID)
                else:
                    del packet.packets[i]
                continue
    #计算得分
    def calcPacketAggGoal(self, packet):
        #这里是计算一个数据包的聚合得分的
        timestamps = []
        for item in packet.packets:
            timestamps.append(item.aggTimestamp)
        timestamps.sort()
        #获得本数据包的时间长度
        t = packet.timestamp
        goal = 0
        #遍历记录的节点信息
        for i in range(len(timestamps)):
            if t == 0:
                goal = goal + pow(10, i) * 9    #直接给最大值
            else:
                if timestamps[i] != 0:
                    # goal = goal + pow(10, i) * int(9 - (timestamps[i] - 1) / t)
                    goal = goal + pow(10, i) * int(9 - (timestamps[i]/ t))
                else:
                    # goal = goal + pow(10, i) * int(9 - timestamps[i] / t)
                    goal = goal + pow(10, i) * 9
        #返回得分
        return goal


        
    #计算聚合损失
    def calcAggLoss(self):
        recvCount = 0
        #获得最大值
        maxGoal = pow(10, self.maxInforInSingleFrm) - 1
        
        loss = 0
        for packet in self.recvs:
            loss = loss + maxGoal - self.calcPacketAggGoal(packet)
            # print(self.calcPacketAggGoal(packet))
            recvCount = recvCount + len(packet.packets)
        #增加上丢失的节点
        # print('丢失'+str(self.nodeCount - recvCount)+'节点')
        # loss = loss + maxGoal * (self.nodeCount - recvCount)  
        lossNcou = self.nodeCount - recvCount
        loglossNcou = 0
        if(lossNcou > 0):
           if(lossNcou < 4):
              loglossNcou = lossNcou*15/self.nodeCount
           else:
              loglossNcou = (math.log(lossNcou)/math.log(50)/10) - 0.02 + (45/49)    
        #计算均方根差
        loss = loss / maxGoal
        #归一
        loss = loss / self.nodeCount 

        loss = loss + loglossNcou

        # 乘以聚合损失在总体损失度函数中的权重调整因子
        loss = loss * self.aggLossPropAdjFactor
        if loss > 1:
           loss = 1
        return loss
    #计算跳数损失
    def calcJumpLoss(self):
        recvCount = 0
        recvedJump = []
        for item in self.recvs:
            for node in item.packets:
                recvedJump.append(node.jump)
                recvCount += 1
        lossJump = 0
        for item in recvedJump:
            lossJump = lossJump + item * item
        # print('丢失'+str(self.nodeCount - recvCount)+'节点')
        lossNcou = self.nodeCount - recvCount
        loglossNcou = 0
        if(lossNcou > 0):
           if(lossNcou < 4):
              loglossNcou = lossNcou*15/self.nodeCount
           else:
              loglossNcou = (math.log(lossNcou)/math.log(50)/10) - 0.02 + (45/49)    
        # lossJump = lossJump + lossNcou*(self.jumpmax * self.jumpmax)
        #综合计算
        lossJump = lossJump / pow(self.jumpmax, 2)
        #归一
        lossJump = lossJump / self.nodeCount 

        lossJump = lossJump + loglossNcou

        # lossJump = lossJump / (2 * self.nodeCount)
        # lossJump = lossJump / (pow(self.nodeCount, 2) / 2)

        # 乘以跳数损失在总体损失度函数中的权重调整因子
        lossJump = lossJump * self.jumpLossPropAdjFactor
        if lossJump > 1:
            lossJump = 1
        return lossJump,(self.nodeCount - recvCount)  

    #计算时间损失
    def calcTimeLoss(self):
        recvCount = 0
        recvedTime = []     #记录数据包接受时间
        #遍历接受到的数据包
        for item in self.recvs:
            #item 是一个数据包
            for node in item.packets:
                #记录数据包的接受时间
                recvedTime.append(node.timestamp)
                recvCount = recvCount + 1
        #计算时间上的损失值使用的是均方差损失函数。
        #接受的时间越长，其损失越大
        lossTime = 0
        #计算收到的数据包的时间损失
        for item in recvedTime:
            lossTime = lossTime + item * item
        #计算未收到的数据包的时间损失
        # print('丢失'+str(self.nodeCount - recvCount)+'节点')
        lossNcou = self.nodeCount - recvCount
        loglossNcou = 0
        if(lossNcou > 0):
           if(lossNcou < 4):
              loglossNcou = lossNcou*15/self.nodeCount
           else:
              loglossNcou = (math.log(lossNcou)/math.log(50)/10) - 0.02 + (45/49)  
        # lossTime = lossTime +  loglossNcou * self.cycleWidth * self.cycleWidth
        #综合计算
        lossTime = lossTime / (pow(self.cycleWidth, 2)) 
        #归于[0,1]
        lossTime = lossTime / self.nodeCount

        lossTime = lossTime + loglossNcou

        # lossTime = lossTime / 5 #缩小它的比例

        # 乘以时间损失在总体损失度函数中的权重调整因子
        lossTime = lossTime * self.timeLossPropAdjFactor
        if lossTime > 1:
           lossTime = 1
 
        return lossTime

    #计算总体损失度函数
    def calcLost(self):

        self.refinePacket()      # 删除重复的数据包

        lost = []  #定义总体损失值向量

        lossTime = self.calcTimeLoss()   # 计算时间损失
        lossQI = self.calcAggLoss()      # 计算聚合损失
        lossJump,lossNode = self.calcJumpLoss()   # 计算跳数损失

        #得到总体损失值向量
        lost.append(lossTime)
        lost.append(lossQI)
        lost.append(lossJump)

        return lost,lossNode

    def getLastStates(self):
        return self.lastLoopRecvs

    def recordStructure(self, stream):
        pass

            
            