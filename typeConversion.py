class TypeConversion(object):
    def __init__(self) -> None:
        pass
    def myStrtoInt(contents):
        linkgroup=[]
        k=-1
        for i in range(1,len(contents)-1):
            if contents[i] == '[':
                linkgroup.append([])
                k = k + 1
            elif contents[i] <= '9' and contents[i] >= '0' : 
                if contents[i-1] <= '9' and contents[i-1] >= '0':
                    continue
                elif contents[i+1] <= '9' and contents[i+1] >= '0':
                    linkgroup[k].append(int(contents[i]+contents[i+1]))
                else:
                    linkgroup[k].append(int(contents[i]))
            else:
                continue
        return linkgroup