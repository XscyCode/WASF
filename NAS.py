import imp
import random
from configure import config
from model import Model
from neuron import States
import numpy as np
import time
import csv
import logger

class BaseAdjust(object):
    def __init__(self, models) -> None:
        self.complete = False
        self.models = models    #模型列表

    def isComplete(self):
        for item in self.models:
            if item.isComplete() == False:
                return False
        return True

    def start(self): pass

class AddedWeight(object):
    def __init__(self, weight, model) -> None:
        self.weight = weight
        self.model = model
        self.model.resetResult()    #开始进行测试了
    
    #计算均方误差
    def rmse(self,value):
        # value = np.array(value)
        # lossweight = np.array([1,1,1])
        # value = ((value) ** 2) * lossweight
        # value = np.sum(value)/np.sum(lossweight)
        # value = np.sqrt(value)
        value = np.array(value)
        value = np.sqrt((value**2).mean)
        return value

    #获取评估结果,这里是取均值 
    def getResult(self):
        return self.model.getResult()

    def getHistoryPower(self):
        # print(self.model.getPower()[:])
        return self.model.getPower()

    #检查是否完成
    def isComplete(self):
        return self.model.isComplete()

#增加的边线
class AddedEdge(object):
    def __init__(self, srcID, desID, models) -> None:
        self.srcID = srcID
        self.desID = desID
        self.models = models
        self.weightTester = []
        for model in models:
            model.addEdge(srcID, desID)
        #开始获取权重，并逐一安排上
        for i in range(len(config.weights)):
            self.models[i].setWeight(srcID, desID, config.weights[i])
            self.weightTester.append(AddedWeight(config.weights[i], self.models[i]))

    def isComplete(self):
        for item in self.weightTester:
            if item.isComplete() == False:
                return False
        #完成了之后，直接恢复原样
        # print(self.models[0].powerlist[:])
        self.doRestore()
        return True

    def getOpResult(self):
        #获取最优的结果，包括结果值，权重.这里假定了所有的任务都已经完成了
        minValue = 1
        minWeight = []
        historyPower = []
        for item in self.weightTester:
            if item.getResult() < minValue:
                minValue = item.getResult()
                minWeight = item.weight
                historyPower = item.getHistoryPower()
                # print(historyPower[:])
        return minValue, minWeight, historyPower

    #恢复models的状态
    def doRestore(self):
        for item in self.models:
            item.delEdge(self.srcID, self.desID)

class AddedNode(object):
    def __init__(self, nodeID, models) -> None:
        self.nodeID = nodeID
        self.models = models     

        #记录自己的最佳结果,默认是1
        self.minValue = 1
        self.srcID = -1
        self.weight = []
        self.historyPower =[]

        #找到自己的所有链接节点
        #如果自己本身是散点，那么直接返回即可
        if self.models[0].getNodeState(self.nodeID) == States.SCATTERED:
            return 
        #不是散点，获取到所有的链接到该节点的其他神经网络节点
        nnConnect = self.models[0].nn.getEdgeToNode(self.nodeID)

        #得到所有链接到这个节点的实质链接，并去掉ID小于当前节点的
        wnConnect = self.models[0].nn.getConnectToNode(self.nodeID)
        if len(wnConnect) == 0:
            return
        
        #查找还没有连接的比自己ID大的节点,有的话，就作为候选
        for item in wnConnect:       
            if (item not in nnConnect) and (item > self.nodeID):
                # print('当前在测试节点{0}将新增的边线'.format(nodeID))
                # print("测试新边候选节点" + str(item))
                # if(self.isSwitchNode(item)):
                    # continue
                #开始测试
                tmp = AddedEdge(item, self.nodeID, self.models)
                #开始测试一条边，对边的测试是多线程的
                while tmp.isComplete() == False:
                    pass
                #获取结果 
                minValue, minWeight ,historyPower= tmp.getOpResult()
                print("本轮测试最小值为" + str(minValue) + ":" + str(minWeight))
                if minValue < self.minValue:
                    self.minValue = minValue
                    self.srcID = item
                    self.weight = minWeight
                    self.historyPower = historyPower
                    # print(historyPower[:])
                print("测试完成")
        return
    
    def isSwitchNode(self,item):
        '''  判断是否需要轮换节点"item" , item 为节点号 ,返回值为True 就轮换'''
        # 初始化
        isSwitch = False
        
        # 获取周围节点
        NodeLink = self.models[0].getNodeLink(item)[:]
        
        # 获取周围节点电量
        powerLink = []
        for nodeidn in NodeLink:
            powerLink.append(self.models[0].powerlist[nodeidn])
        powerLink.append(self.models[0].powerlist[item])
        
        # 判断当前节点电量是否符合筛选条件
        if powerLink[-1] + 4 < np.array(powerLink).mean() :
            isSwitch = True
            
        return isSwitch

    def getOpResult(self):
        return self.srcID, self.nodeID, self.weight, self.minValue, self.historyPower                                                                                                  
    
class AddEdge(BaseAdjust):

    def start(self, lastLoss):
        
        self.lastLoss = lastLoss
        recordStream = open(config.recordStructFile, 'a+')

        #开始工作,先设置增加ID
        self.curNode = AddedNode(0, self.models)

        while True:
            opSrcID, opDesID, opWeight, value, history = self.curNode.getOpResult()
            if value < self.lastLoss:
                print('发现更小损失 {}'.format(value))
                recordStream.write('obtain a smaller loss {}\n'.format(value))
                self.lastLoss = value
                #同步修改所有的节点信息
                for item in self.models:
                    item.addEdge(opSrcID, opDesID)
                    item.setWeight(opSrcID, opDesID, opWeight)
                    item.setLastLoss(value)
                    item.setPower(history)

                #记录信息                           
                recordStream.write('***************' + time.strftime('%m-%d %H:%M:%S') + '*************************\n')
                self.models[0].recordStructure(recordStream)

                #将下一个终点设置为本节点,并开始进行测试
                self.curNode = AddedNode(opSrcID, self.models)
            #然后继续寻找下一个节点，直到完成
            #现在的结果并不比之前的好
            else:
                #这里有一些判断条件，如果达到了末尾，那么退出，否则随机的选择一个节点
                temp = self.models[0].getConnectToNode(self.curNode.nodeID)
                wnConnect = []
                for item in temp:
                    if item > self.curNode.nodeID:
                        wnConnect.append(item)

                if len(wnConnect) == 0:
                    #本次添加器已经完成了工作, 直接返回就可以了
                    print('本次增加测试已经完成')
                    recordStream.flush()
                    recordStream.close()
                    return

                #没有到头，那就找一个电量最高的
                # randomValue = random.randint(0,len(wnConnect) - 1)
                ipowerlist = []
                for ipower in wnConnect:
                    ipowerlist.append(self.models[0].powerlist[ipower])
                maxpower = max(ipowerlist)
                maxindex = ipowerlist.index(maxpower)
                #logger.logger.debug('延长至节点' + str(wnConnect[randomValue]))
                self.curNode = AddedNode(wnConnect[maxindex], self.models)

#增加的边线
class adjustEdgeWeightWorker(object):
    def __init__(self, edge, models) -> None:
        self.srcID = edge.fromID
        self.desID = edge.toID
        self.models = models
        self.lastWeight = edge.getWeight()
        self.weightTester = []

        #开始获取权重，并逐一安排上
        for i in range(len(config.weights)):
            self.models[i].setWeight(self.srcID, self.desID, config.weights[i])
            self.weightTester.append(AddedWeight(config.weights[i], self.models[i]))

    def isComplete(self):
        for item in self.weightTester:
            if item.isComplete() == False:
                return False
        #完成了之后，直接恢复原样
        self.doRestore()
        return True

    def getOpResult(self):
        #获取最优的结果，包括结果值，权重.这里假定了所有的任务都已经完成了
        minValue = 1
        minWeight = []
        for item in self.weightTester:
            if item.getResult() < minValue:
                minValue = item.getResult()
                minWeight = item.weight
                historyPower = item.getHistoryPower()
        return minValue, minWeight,historyPower

    #恢复models的状态
    def doRestore(self):
        for item in self.models:
            item.setWeight(self.srcID, self.desID, self.lastWeight)

class adjustEdgeWeight(BaseAdjust):
    def start(self, lossValue, nodeID):
        #这个是调整一个节点的边线的权重
        #首先是遍历这个节点的所有边，然后遍历所有的权重组
        self.lossValue = lossValue
        self.adjNodeID = nodeID
        print("开始调整轮换节点权重： {}".format(self.adjNodeID))
        es = self.models[0].getEdges(self.adjNodeID)
        for item in es:
            #调整权重，然后开始跑起来看看结果
            adj = adjustEdgeWeightWorker(item, self.models)
            while adj.isComplete() == False:
                pass
            #这里就是调整完成了，获取数值
            minValue, minWeight, myhistoryPower = adj.getOpResult()
            if minValue < self.lossValue:
                self.lossValue = minValue
                print("调整权重时发现更小损失值: {}".format(minValue))
                #开始遍历调整模型
                for mod in self.models:
                    mod.setWeight(item.fromID, item.toID, minWeight)
                    mod.setPower(myhistoryPower)
        return

class delEdge(BaseAdjust):
    def start(self, lossValue, nodeID):
        self.lossValue = lossValue
        self.adjNodeID = nodeID
        #获取到这个节点的所有的边线，然后删除它们，看看效果怎么样
        print("开始尝试删除节点边线{}".format(self.adjNodeID))
        es = self.models[0].getEdges(self.adjNodeID)
        for item in es:
            #删除边线，然后看看效果怎么样
            self.models[0].delEdge(item.fromID, item.toID)
            self.models[0].resetResult() 
            while self.models[0].isComplete() == False:
                pass
            #获取结果
            result = self.models[0].getResult()
            #计算均方误差
            result0 = np.array(result)
            result1 = np.sqrt(((result0) ** 2).mean())
            if result1 < self.lossValue:
                print('发现更小损失:{}'.format(result1))
                self.lossValue = result1
                for i in range(1, 4, 1):
                    self.models[i].delEdge(item.fromID, item.toID)
            else:
                #恢复原来的
                self.models[0].addEdge(item.fromID, item.toID)
                self.models[0].setWeight(item.fromID, item.toID, item.getWeight())

class adjustWeight(BaseAdjust):
    def start(self, lossValue,adjNodeID):
        self.lossValue = lossValue
        #随机选择一个节点作为调整权重的节点
        self.adjNodeID = adjNodeID

        print('选择{0}作为调整权重节点'.format(self.adjNodeID))

        #无需记录旧有的权重，因为一定在覆盖范围内

        #准备开始调整权重
        self.weights = config.weights
        self.testResults = []
        for i in range(len(self.weights)):
            self.models[i].setSelfWeight(self.adjNodeID, self.weights[i])
            self.models[i].setLastLoss(lossValue)
            self.models[i].resetResult()         

        while True:
            hasDone = True
            for item in self.models:
                if item.isComplete() == False:
                    hasDone = False
            if hasDone == True:
                break
        
        #已经测试完成，现在开始检查各个结果
        minValue = 1
        minIndex = -1
        for i in range(len(self.models)):
            if self.models[i].getResult() < minValue:
                minValue = self.models[i].getResult()
                minIndex = i
                powerlist = self.models[i].getPower()
        #统一更新所有的模型
        # print(powerlist[:])
        for item in self.models:
            item.setSelfWeight(self.adjNodeID, self.weights[minIndex])
            item.setPower(powerlist)
        #记录
        if minValue < self.lossValue:
            self.lossValue = minValue
            stream = open(config.recordStructFile, 'a+')
            stream.write('***************' + time.strftime('%m-%d %H:%M:%S') + '*************************\n')
            self.models[0].recordStructure(stream)
            stream.flush()
            stream.close()
            print('发现最佳损失值为{0}'.format(minValue))
        
class NAS(object):
    def __init__(self, models) -> None:
        self.lastLost = 1       #最后的损失值
        self.models = models    #模型
        self.NodeStateList = []
        # print(len(self.models))
        if len(self.models) != len(config.weights):
            raise Exception('模型个数不对')

    def recordList(self,list):
        logger.mkdir('.\powerFile\\' + 'Power-' + time.strftime('%m-%d'))
        fileName = '.\powerFile\\' + 'Power-' + time.strftime('%m-%d') + '\\'+ time.strftime('%H' + '.csv')
        with open(fileName, 'a+', newline='') as f:
            f.write('******************************************************\n')
            f.write('this is the current power\t')
            f.write(time.strftime('%m-%d %H:%M:%S'))
            f.write('\n')
            writer = csv.writer(f)
            writer.writerow(list)
    # 查询列表中的节点电量后按电量由低到高排序
    def sortPower(self,twoNode):
        resultpower = []
        for nodeitem in twoNode:
            resultpower.append((self.models[0].powerlist[nodeitem],nodeitem))
        resultpower.sort()
        return resultpower   # 返回值为列表，最大电量节点应取返回值中的最后一个节点
    # 查找单个可轮换节点
    def FindSingleSwitchNode(self,frontNodeLink,behindNodeLink,targetNode):
        '''
        函数：查找单个可轮换节点。  frontNodeLink:候选节点区间前端节点的联通集,
        behindNodeLink:候选节点区间末端节点的联通集,targetNode:候选能量合格节点集合
        '''
        # 初始化
        isGet = False
        resultpower = [(-1,-1)]
        # 先在当前节点的上下节点联通集中寻找共同节点
        commonNode = list(frontNodeLink.intersection(behindNodeLink))
        #如果commonNode不为空，找到其中是否存在能量合格的节点
        if not commonNode == []:
            resultSingle = set(commonNode).intersection(set(targetNode))
            resultSingle = list(resultSingle)
            # resultSingle不为空，即存在能量合格节点,说明找到可单个轮换节点
            if not resultSingle == []:
                resultpower = self.sortPower(resultSingle)[:]
                isGet = True
        return isGet,resultpower[-1][1]
    # 查找两个节点进行轮换
    def FindTwoSwitchNode(self,frontNodeLink,behindNodeLink,targetNode):
        # 初始化
        isGet = False
        result= (-1,-1)
        # 在前后节点的联通集中寻找能量合格节点
        frontPowerNode = list(frontNodeLink.intersection(set(targetNode)))
        behindPowerNode = behindNodeLink.intersection(set(targetNode))
        frontPowerNode.sort(reverse=True)
        
        # 从前端节点联通集内的最大号节点的联通集开始查起，是否与后端节点的联通集存在交集
        for item in frontPowerNode:
            itemLink = set(self.models[0].getNodeLink(item))
            twoNode = list(itemLink.intersection(behindPowerNode))
            if not twoNode == []:  # 存在交集，找到两个节点组合
                resultpower = self.sortPower(twoNode)[:]
                result =(item,resultpower[-1][1])
                isGet = True
                break
        return isGet,result
    # 开始查找轮换节点 
    def startFind(self,currentIndex,behindrange):
        # 获取前后端节点以及中间节点
        frontNode = self.NodeStateList[currentIndex-1]
        behindNode = self.NodeStateList[currentIndex+behindrange]
        NodesBetween = list(range(frontNode,behindNode+1,1))[:]

        # 接下来要在中间节点内找到目标普通节点
        # 目标普通节点需求是 1、能量较高，2、能够通信

        # 先获取中间所有普通节点的剩余电量
        NodesPower = []
        for node in NodesBetween:
            NodesPower.append(self.models[0].powerlist[node])

        # 首要需求是能量，而且要避免出现 节点在能够通信的节点间一直轮换 的情况
        # 先找满足能力要求的节点，这里只要不是能量最低的几个节点即可
        # 定义较为宽松的条件：大于均值即可
        # 获取能量合格的目标普通节点
        targetNode = []
        powerMean = np.array(NodesPower).mean()
        for i in range(len(NodesBetween)):
            if NodesPower[i] >= powerMean:
                targetNode.append(NodesBetween[i])

        # 然后获取前后端节点的联通集
        frontNodeLink = set(self.models[0].getNodeLink(frontNode))
        behindNodeLink = set(self.models[0].getNodeLink(behindNode))
        
        # 开始寻找单个轮换节点
        isget,result = self.FindSingleSwitchNode(frontNodeLink,behindNodeLink,targetNode)
        if (isget): # 存在单个节点轮换
            resultNode = (frontNode,result,behindNode)
            return resultNode

        # 不存在单个轮换节点，找两个节点替换
        isget,result = self.FindTwoSwitchNode(frontNodeLink,behindNodeLink,targetNode)
        if (isget): # 选两个节点构建通信链路
            resultNode = (frontNode,result[0],result[1],behindNode)
            return resultNode 

        # 两节点组合也找不到
        return None
    # 是否轮换该节点
    def isSwitchNode(self,item):
        '''  判断是否需要轮换节点"item" , item 为节点号 ,返回值为True 就轮换'''
        # 初始化
        isSwitch = False
        
        # 获取周围节点
        NodeLink = self.models[0].getNodeLink(item)[:]
        
        # 获取周围节点电量
        powerLink = []
        for nodeidn in NodeLink:
            powerLink.append(self.models[0].powerlist[nodeidn])
        powerLink.append(self.models[0].powerlist[item])
        
        # 判断当前节点电量是否符合轮换条件
        if powerLink[-1] + 8 < np.array(powerLink).mean() :
            isSwitch = True
            
        return isSwitch
    
    def delnode(self,item):
        # 先删除该节点发出的连接,双向都删
        es = self.models[0].getEdges(item)
        for edgenode in es:
          # 删除边线，更新到所有模型
            # print(edgenode.fromID, edgenode.toID)
            for imodel in range(4):
                self.models[imodel].delEdge(edgenode.fromID, edgenode.toID)
                # 反向连接也删一下试试
                self.models[imodel].delEdge(edgenode.toID, edgenode.fromID)
        # 还得找一下附近节点是否有链接到本节点的,直接删就行，不存在时自动返回
        itemindex = self.NodeStateList.index(item)
        for imodel in range(4):
            for indexcc in range(1,4):
                self.models[imodel].delEdge(self.NodeStateList[itemindex-indexcc], item)
                self.models[imodel].delEdge(self.NodeStateList[itemindex+indexcc], item)

    def addnode(self,srcNode,desNode):
        for imodel in range(4):    
            self.models[imodel].addEdge(srcNode, desNode)
            self.models[imodel].setWeight(srcNode, desNode, [0.2,0.2,0.2])

    def PowerSwitchNode(self,lastLost):
        self.NodeStateList.clear()
        newlastLost = lastLost
        for i  in range(50):  
            if self.models[0].getNodeState(i) == States.CONNECTED:
               self.NodeStateList.append(i)     
        for item in self.NodeStateList:
            if(self.isSwitchNode(item)):
                print("节点"+str(item)+"电量较低需要轮换")               
                # 获取当前需要轮换节点位置
                currentIndex = self.NodeStateList.index(item)
                # 为了防止聚合节点越轮换越密，先在大范围查找可轮换节点
                # 扩大到后两节点
                behindrange = 2
                result = self.startFind(currentIndex,behindrange)
                if not result == None:
                    # resultNode.append(result)
                    self.delnode(item)
                    newlastLost = 1       # 发生节点轮换直接重置网络损失值
                    if len(result) < 4:
                       print(result)
                       self.addnode(result[2],result[1])
                       self.addnode(result[1],result[0])
                       adSWnode = adjustEdgeWeight(self.models)
                       for i in range(1,3):
                          adSWnode.start(lastLost,result[i])
                          newlastLost = adSWnode.lossValue
                    else:
                       print(result)
                       self.addnode(result[3],result[2])
                       self.addnode(result[2],result[1])
                       self.addnode(result[1],result[0]) 
                       adSWnode = adjustEdgeWeight(self.models)
                       for i in range(1,4):
                          adSWnode.start(lastLost,result[i])
                          newlastLost = adSWnode.lossValue
                else:
                    behindrange = 1   # 缩小轮换节点范围
                    result = self.startFind(currentIndex,behindrange)
                    if not result == None:
                        # resultNode.append(result)
                       self.delnode(item)
                       newlastLost = 1       # 发生节点轮换直接重置网络损失值
                       if len(result) < 4:
                          print(result)
                          self.addnode(result[2],result[1])
                          self.addnode(result[1],result[0])
                          adSWnode = adjustEdgeWeight(self.models)
                          for i in range(1,3):
                            adSWnode.start(lastLost,result[i])
                            newlastLost = adSWnode.lossValue
                       else:
                          print(result)
                          self.addnode(result[3],result[2])
                          self.addnode(result[2],result[1])
                          self.addnode(result[1],result[0])
                          adSWnode = adjustEdgeWeight(self.models)
                          for i in range(1,4):
                            adSWnode.start(lastLost,result[i])
                            newlastLost = adSWnode.lossValue
        
        return newlastLost

    def doTest(self):
        lastLost = 1
        while True:
            #增加边
            # print(self.models[0].wn.PowerGroup[:])
            adder = AddEdge(self.models)
            adder.start(lastLost)
            lastLost = adder.lastLoss
            self.recordList(self.models[0].powerlist[:])

            # for i  in range(50):  
            #   if self.models[0].getNodeState(i) == States.CONNECTED:
            #      self.NodeStateList.append(i) 
            # print(self.NodeStateList)
            # self.NodeStateList.clear()
            # lastLost = self.PowerSwitchNode(lastLost)
            # nodeedge = self.models[0].getEdges(5)

            adj = adjustWeight(self.models)
            adjnodeid = random.randint(1, config.nodeCount - 1)
            adj.start(lastLost,adjnodeid)
            lastLost = adj.lossValue
            print("调整节点{}权重完成，最佳损失值为{}".format(adjnodeid,lastLost))

            # newPort = input('请输入新的调整比例:')
            # newP = newPort.split(',')
            # for item in self.models:
            #     item.setP(float(newP[0]), float(newP[1]), float(newP[2]))
            
            #for i in range(config.nodeCount - 1, 1, -1):
            # adj = adjustEdgeWeight(self.models)
            # adj.start(lastLost, i)
            # lastLost = adj.lossValue
            # print("调整边线权重{}完成，最佳损失值为{}".format(i, lastLost))

            # adj = delEdge(self.models)
            # adj.start(lastLost, i)
            # lastLost = adj.lossValue
            # print("删除边线{}完成，最佳损失值为{}".format(i, lastLost))
            
            # adj = adjustEdgeWeight(self.models)
            # for i in range(config.nodeCount - 1, 1, -1):
            #     adj.start(lastLost, i)
            #     lastLost = adj.lossValue
            # print("调整边线权重完成，最佳损失值为{}".format(lastLost))
            
            # adj = adjustWeight(self.models)
            # for i in range(config.nodeCount - 1, 1, -1):
            #     adj.start(lastLost, i)
            #     lastLost = adj.lossValue
            # print('调整自身权重完成，最佳损失值为{}'.format(lastLost))
