import random
from configure import config

class neuronWeight(object):
    def __init__(self, weight = None) -> None:
        if weight == None:
            # weightColCount = config.weightColCount
            self.weight = [0.2,0.2,0.2]
            # for i in range(weightColCount):
            # self.weight.append(random.random())
        else:
            self.weight = weight

    def getWeight(self):
        return self.weight

    def setWeight(self, weight):
        #默认是按照顺序来
        self.weight = weight