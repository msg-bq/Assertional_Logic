from experta import *

def W_GetHash(self):
    return 'ANY' #设置参数值的时候避开这个，或者这里换一个

W.GetHash = W_GetHash

def L_GetHash(self):
    return self.value()

L.GetHash = L_GetHash