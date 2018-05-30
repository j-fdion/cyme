"""
Composants reliés au stochastique.
----------------------------------
"""

import random, math
from bisect import bisect
from collections import defaultdict
from abc import ABCMeta, abstractmethod

from .. import ecs
from . import base
from . import kanban

class Echantillonnage(metaclass=ABCMeta):

    @abstractmethod
    def get(self):
        print("Echantillonnage's get() method was called.")

    def test(self,nom=""):
        print("Test de l'échantillonnage",type(self).__name__,nom)
        print("Exemple de valeurs:",self.get(),self.get(),self.get(),self.get(),self.get(),
               self.get(),self.get(),self.get(),self.get(),self.get(),self.get(),self.get())
        x=0.0
        k=1000000
        for i in range(k):
            x+=self.get()
        x/=k
        print("Moyenne sur",k,"essais:",x)
        return x


class ConstantValue(Echantillonnage):

    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value


class TriggerFrequence(Echantillonnage):

    def __init__(self, freq):
        self.freq=freq

    def get(self):
        return random.random()<=self.freq
    

class TriangularDistributionSample(Echantillonnage):

    def __init__(self, low, high, mode):
        self.low = low
        self.high = high
        self.mode = mode

    def get(self):
        return random.triangular(self.low, self.high, self.mode)


class FrequencyDistributionSample(Echantillonnage):

    def __init__(self, x, f):
        self.x = x # tableau des valeurs
        self.f = f # tableau des frequences 
        self.m = len(x) # nb de valeurs differentes dans x
        self.fc = [0]*self.m # tableau des frequences cumules
        if self.m != len(f): print("Erreur FrequencyDistributionSample init: tableaux de tailles differentes.")
        self.n=0
        for i in range(self.m):
          self.n+=self.f[i]
          self.fc[i]=self.n

    def get(self):
        v = random.randint(1, self.n)
        for i in range(self.m):
            if v<=self.fc[i]: break
        return self.x[i]


class NonParametricNaiveSample(Echantillonnage):

    def __init__(self, x):
        self.x = x # tableau des valeurs
        self.n = len(x) # nb de valeurs dans x

    def get(self):
        return self.x[random.randrange(self.n)]


class NonParametricKDESample(Echantillonnage):

    def __init__(self, x):
        self.x = x # tableau des valeurs
        self.n = len(x) # nb de valeurs dans x
        self.m = 0
        self.s = 0
        self.h=0.0
        if self.n>1:
            self.m = sum(self.x)/self.n
            self.s = math.sqrt( sum([(xi - self.m)**2 for xi in self.x]) / (self.n-1) ) # ecart-type
            #self.h = 1.059*s*self.n**-0.2  # kernel loi normale
            self.h = 2.34*self.s*self.n**-0.2  # kernel loi parabolique
            print("n,m,s,h=",self.n,self.m,self.s,self.h)

    def get(self): 
        v = self.x[random.randrange(self.n)]
        w = 0.0
        for i in range(10): # on essai 10x, sinon on prends 0
            u=random.random()
            w=random.uniform(-1.0,1.0)
            if u<=(1.0-w*w):
                break
        # on limite la bandwidth a 50% de variation max de la valeur
        hh=0.5*v
        if self.h<hh: hh=self.h
        return round(v+w*hh) # force entier


class Stochastique(ecs.Component):

    def __init__(self, cible):
        self.trigger_events = {}
        self.trigger = False
        self.cible = cible

    def add_event(self, name, p, te, pe):
        self.trigger_events[name] = (p, list(zip(te,pe)))

    def remove_event(self, name):
        del self.trigger_events[name]


class EventStochastique(ecs.System):

    def __init__(self, seed = -1):
        super().__init__()
        if seed == -1:
            seed=random.randint(0, 1999999717)
        print("Racine:",seed)
        random.seed(seed)

    def reset(self):
        pass

    def init(self):
        pass

    def update(self, dt):

        for entity, sto in self.entity_manager.pairs_for_type(Stochastique):
            for event in sto.trigger_events.values():
                p, choices = event
                u = random.random()
                if u <= p:
                    #sto.trigger = True
                #if sto.cible.actif and sto.cible.utilisable and sto.trigger:
                    #sto.trigger = False
                    choice = self.weighted_choice(choices)
                    sto.cible.temps_event = choice.get()
                    bris = kanban.DelayedKanban("BRIS")
                    bris.duree = choice.get() * 60 #Events en minute alors on multiplie par 60 pour avoir les secondes
                    sto.cible.bris.append(bris)
                    break

    def weighted_choice(self, choices):
        weights, values = zip(*choices)
        total = 0
        cumulative_weights = []
        for w in weights:
            total += w
            cumulative_weights.append(total)
        x = random.random() * total
        i = bisect(cumulative_weights, x)
        return values[i]

