import logging
import time
import os

def mkdir(folderName):
    if not os.path.exists(folderName):
       os.makedirs(folderName)

class Logger(object):
    _instance = {}
    def __init__(self) -> None:
        self.logger = logging.getLogger('sdann')
        self.logger.setLevel(level=logging.DEBUG)
        mkdir('.\logFile\\' + 'Log-' + time.strftime('%m-%d'))
        fileName = '.\logFile\\' + 'Log-' + time.strftime('%m-%d') + '\\'+ time.strftime('%H.%M' + '.txt')
        self.handle = logging.FileHandler(fileName, encoding="utf-8",mode="a")
        self.handle.setLevel(logging.DEBUG)

        self.formatter = logging.Formatter('%(asctime)s - %(message)s')
        self.handle.setFormatter(self.formatter)

        self.logger.addHandler(self.handle)

logger = Logger()