import matplotlib.pyplot as plt
import math
import numpy as np
plt.rcParams["font.sans-serif"]=["SimHei"] #设置字体
plt.rcParams["axes.unicode_minus"]=False #该语句解决图像中的“-”负号的乱码问题

class getresult():
  def __init__(self,filename) -> None:
     self.filename = filename
     self.timecon = []
     self.jumpcon = []

  def getTimeWithJump(self):
      file = open(self.filename,'r',encoding='utf-8')
      content = file.readlines()
      lastResultTop = 0
      for i in range(len(content)):
        if content[i].find('--------') != -1:
           lastResultTop = i   

      for i in range(lastResultTop + 4,len(content)-1,1):
        contents = content[i].split(' ')
        for k in range(5,len(contents)-1,1):
          contensss = contents[k].split(':')
          self.timecon.append(int(contensss[1]))
          self.jumpcon.append(int(contensss[2].split(',')[0]))

      return self.timecon, self.jumpcon

class showresult():
  def __init__(self) -> None:
     self.curveNum = 0
     self.Lables = []
  
  def showScatterOfig(self,argument,FuncCurve,LableS):
      plt.figure(LableS)
      plt.scatter(argument,FuncCurve,color='#5B00AE',marker = 's') 
      # plt.plot(self.x+5,self.y,'o--',color="red",linewidth=3.0, markersize = 8 )
      plt.legend(labels=(LableS,),loc = 'upper right', markerscale = 1, fontsize = 25)  #图例
      

  def showScatterSfig(self,argument,FuncCurve,LableS):
      self.curveNum += 1
      self.Lables.append(LableS)
      if(self.curveNum == 1):
          plt.subplot(121)
          # plt.scatter(argument,FuncCurve,color='#5B00AE',marker = 's') 
          plt.hist(FuncCurve,bins=[0,50,100,150,200,250,300],color='#5B00AE',edgecolor='black',density=True)
      # plt.plot(self.x+5,self.y,'o--',color="red",linewidth=3.0, markersize = 8 )
          plt.legend(labels=(LableS,),loc = 'upper right', markerscale = 1, fontsize = 25)  #图例
      if(self.curveNum == 2):
          plt.subplot(122)
          # plt.scatter(argument,FuncCurve,color='#FF69B4',marker = 'o') 
          plt.hist(FuncCurve,bins=[0,2,4,6,8,10],histtype='bar',edgecolor='black',density=True)
          plt.legend(labels=(self.Lables[0],self.Lables[1]),loc = 'upper right', markerscale = 1, fontsize = 25)
  
  # def showScatterSplot(self,argument,FuncCurve,LableS):
    

  def showStart(self):
    plt.show()
     


if __name__ == '__main__':
  r1 = getresult('.\logFile\\Log-10-27\\18.06.txt')
  timelist,jumplist = r1.getTimeWithJump()
  S1 = showresult()
  argux = np.arange(1,len(timelist)+1,1)
  S1.showScatterSfig(argux,timelist,'aggtime')
  argux = np.arange(1,len(jumplist)+1,1)
  S1.showScatterSfig(argux,jumplist,'jump')
  S1.showStart()
