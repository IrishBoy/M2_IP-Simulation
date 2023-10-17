import sys
import numpy as np
import random
import matplotlib.pyplot as plt
from matplotlib import  colors
import math

import pandas as pd
import simpy
import queue

def printLossRate(env, source):
    global df_lossRates
    source.cpterPrintLR += 1
    if source.cpterPrintLR == periodPrintLR:
        source.cpterPrintLR = 0
        print("loss", env.now, source.ident, source.queueLosses/source.nbEmissions)
        df_lossRates.loc[len(df_lossRates)] = {'sourceId': source.ident, 'time':env.now, 'lossRate':source.queueLosses/source.nbEmissions}



class packet(object):
    def __init__(self, t, ident, pktSize):
        global seqno
        seqno += 1
        self.t = t
        self.ident = ident
        self.pktSize = pktSize
        self.seqno = seqno

class queueClass(object):
    def __init__(self, env, queueCapa, serviceRate):
        self.env = env
        self.inService = 0
        self.buffer = queue.Queue(maxsize = queueCapa)
        self.queueLenght = 0
        self.queueCapacity = queueCapa
        self.serviceRate = serviceRate
        self.lastChange = 0
        self.cpterPrintLR = 0


    def service(self):
        p = self.buffer.get()
        print('%s arriving' % (p.seqno))
        self.inService = 1
        yield self.env.timeout(1.0 / self.serviceRate)
        self.queueLenght -= p.pktSize
        del p
        if self.queueLenght > 0:
            self.env.process(self.service())
        else:
            self.inService = 0
    
    def reception(self, source, pkt):
        if self.queueLenght + pkt.pktSize < self.queueCapacity:
            self.queueLenght += pkt.pktSize
            self.buffer.put(pkt)
            if self.inService == 0:
                self.env.process(self.service())
        else:
            printLossRate(self.env, source)
            print(f'''Loss at {self.env.now}''')
            source.queueLosses += 1
            del pkt
            
            



class poissonSource(object):
    def __init__(self, env, rate, q, ident, pktSize):
        self.env = env
        self.rate = rate
        self.q = q
        self.ident = ident
        self.pktSize = pktSize
        self.nbEmissions = 0
        self.queueLosses = 0
        self.cpterPrintLR = 0
        self.action = env.process(self.run())

    
    def run(self):
        while True:
            yield self.env.timeout(1/ self.rate)
            p = packet(self.env.now, self.ident, self.pktSize)
            self.nbEmissions += 1
            self.q.reception(self, p)
            



simulationDuration = 1000
periodPrintLR = 10

df_lossRates = pd.DataFrame(columns=['sourceId', 'time', 'lossRate'])

seqno = 0

np.random.seed(11)



env = simpy.Environment()

q = queueClass(env, 10, 1.0)
ps1 = poissonSource(env, 10, q, 1, 1)

env.run(until = simulationDuration)

plt.plot(df_lossRates[df_lossRates['sourceId'] == 1]['time'], df_lossRates[df_lossRates['sourceId'] == 1]['lossRate'], linewidth = 1, label = 'Source 1')
plt.grid(True, which = "both", linestyle = 'dotted')
plt.ylim(ymin = 0)
plt.ylabel('Loss rate')
plt.xlabel('Time units')

plt.title('Loss rate in function of the time')

plt.legend()

# plt.savefig('myfig.pdf')
# plt.show()

print(df_lossRates)


