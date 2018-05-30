"""
Behavior tree des machines.
---------------------------
"""

from .. import bt


class preTache(bt.Task):
    def __init__(self, machine, k=1):
        super().__init__()
        self.machine=machine
        self.k=k # nb traite

    def run(self):
        #print("action: machinePreTache")
        return bt.Task.SUCCES


class machineTache(bt.Task):
    def __init__(self, machine, k=1):
        super().__init__()
        self.machine=machine
        self.k=k # nb traite

    def run(self):
        #print("action: machineTache")
        return bt.Task.SUCCES


class postTache(bt.Task):
    def __init__(self, machine):
        """:param machine: un composant avec un handle sur un ``Noeud``. """
        super().__init__()
        self.machine=machine

    def run(self):
        #print("action: postTache")
        err = False
        ok = True
        # on revalide que le materiel est encore dispo en entree
        for idx in range(len(self.machine.noeud.ina)):
            accumulateur = self.machine.noeud.ina[idx].accumulateur
            if not accumulateur.dispo()>=self.machine.qin[idx]: ok = False
        if not ok: # zut... on a perdu du temps :(
            err=True
        else: # le materiel est encore present en entree et il y a de la place en sortie
            for idx in range(len(self.machine.noeud.ina)):
                accumulateur = self.machine.noeud.ina[idx].accumulateur
                done = accumulateur.rm(self.machine.qin[idx])
                if not done:
                    print("Erreur", type(self), "rm item(s) non-existant?")
                    err=True
            for idx in range(len(self.machine.noeud.oua)):
                accumulateur = self.machine.noeud.oua[idx].accumulateur
                done = accumulateur.add(self.machine.qout[idx])
                if not done:
                    print("Erreur", type(self), "echec add item(s)?")
                    err=True
        if err: 
            self.machine.travail_perdu += self.machine.tcycle
            return bt.Task.ECHEC
        else:
            self.machine.x+=self.machine.qin_total_par_cycle
            self.machine.xout+=self.machine.qout_total_par_cycle
            return bt.Task.SUCCES


class entreeTest_i(bt.Task):
    """ True si au moins k items dispo sur le idx-ème accumulateur en entree. """

    def __init__(self, machine, accumulateur, k=1):
        """:param machine: un composant avec un handle sur un ``Noeud``
        :param accumulateur: accumulateur a tester
        :param k: nombre minimal d'éléments """
        super().__init__()
        self.machine=machine
        self.accumulateur=accumulateur
        self.k=k # nb items

    def run(self):
        if self.accumulateur.dispo()>=self.k:
            return bt.Task.SUCCES
        return bt.Task.ECHEC


class sortieTest_i(bt.Task):
    """ True si au moins k places dispo sur le idx-ème accumulateur en sortie. """

    def __init__(self, machine, accumulateur, k=1):
        """:param machine: un composant avec un handle sur un ``Noeud``
        :param accumulateur: accumulateur a tester
        :param k: nombre minimal de places """
        super().__init__()
        self.machine=machine
        self.accumulateur=accumulateur
        self.k=k # nb places

    def run(self):
        if not self.accumulateur.full(self.k):
            return bt.Task.SUCCES
        return bt.Task.ECHEC

