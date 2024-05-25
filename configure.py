import configparser

class configureReader(object):
    _instance = {}
    def __init__(self) -> None:
        self.weights = self.getWeightConfig()
        self.weightColCount = self.getWeightColCount()
        self.testCount = self.getTestCountConfig()
        self.nodeCount = self.getNodeCount()
        self.maxQIInFrm = self.getMaxQIInFrm()
        self.dataGeneralCycle = self.getDataGeneralCycle()
        self.slotPerSec = self.getSlotPerSec()
        self.connectRangeMin = self.getConnectRangeMin()
        self.connectRangeMax = self.getConnectRangeMax()
        self.maxLiveTime = self.getMaxLiveTime()
        self.recordStructFile = self.getRecordFileName()
    #读取权重配置
    def getWeightConfig(self):
        cf = configparser.ConfigParser()
        cf.read('configure.ini')
        weightCount = cf.get('weight', 'weightTestGroupCount')
        weights = []
        for i in range(int(weightCount)):
            weightItem = cf.get('weight', 'weight' + str(i))
            weightStrSplit = weightItem.split(',')
            weightNew = []
            for item in weightStrSplit:
                weightNew.append(float(item))
            weights.append(weightNew)
        return weights
    #读取节点初始化权重
    def getWeightNodeInit(self):
        cf = configparser.ConfigParser()
        cf.read('configure.ini')
        weightNodeInit = []
        weightNodeInit = cf.get('weight','weightNodeInit')
        return weightNodeInit

    #读取权重列数
    def getWeightColCount(self):
        cf = configparser.ConfigParser()
        cf.read('configure.ini')
        weightCount = cf.get('weight', 'weightColCount')
        return int(weightCount)

    #读取测试次数
    def getTestCountConfig(self):
        cf = configparser.ConfigParser()
        cf.read('configure.ini')
        testCount = cf.get('test', 'testCount')
        return int(testCount)

    #读取节点个数
    def getNodeCount(self):
        cf = configparser.ConfigParser()
        cf.read('configure.ini')
        result = cf.get('node', 'count')
        return int(result)

    #读取单帧最大QI
    def getMaxQIInFrm(self):
        cf = configparser.ConfigParser()
        cf.read('configure.ini')
        result = cf.get('system', 'maxQIInFrm')
        return int(result)

    #数据产生周期
    def getDataGeneralCycle(self):
        cf = configparser.ConfigParser()
        cf.read('configure.ini')
        result = cf.get('node', 'dataGeneralCycle')
        return int(result)

    #每秒分为多少个段
    def getSlotPerSec(self):
        cf = configparser.ConfigParser()
        cf.read('configure.ini')
        result = cf.get('system', 'slotPerSecond')
        return int(result)

    #节点的连接范围
    def getConnectRangeMin(self):
        cf = configparser.ConfigParser()
        cf.read('configure.ini')
        result = cf.get('node', 'connectRangeMin')
        return int(result)
       #节点的连接范围
    def getConnectRangeMax(self):
        cf = configparser.ConfigParser()
        cf.read('configure.ini')
        result = cf.get('node', 'connectRangeMax')
        return int(result)

    #数据最多存活时间
    def getMaxLiveTime(self):
        cf = configparser.ConfigParser()
        cf.read('configure.ini')
        result = cf.get('system', 'maxLiveTime')
        return int(result)

    def getRecordFileName(self):
        cf = configparser.ConfigParser()
        cf.read('configure.ini')
        result = cf.get('system', 'recordStructureFileName')
        return result

config = configureReader()