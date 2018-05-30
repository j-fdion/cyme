"""
Behavior tree des mobiles.
--------------------------
"""

import random

from .. import bt
from .. import simulation


class isNDestBloque(bt.Task):
    """ Vérifie si le noeud de destination n'est pas bloque. """
    def __init__(self, mobile):
        super().__init__()
        self.mobile = mobile

    def run(self):
        """
        :return: ``bt.Task.SUCCES`` si le noeud de destination n'est pas bloque.
        """
        if self.mobile.ndest is None:
            return bt.Task.SUCCES
        else:
            if self.mobile.ndest != self.mobile.npos:
                value = bt.Task.SUCCES if not self.mobile.ndest.bloque else bt.Task.ECHEC
                return value
            else:
                return bt.Task.SUCCES


class jumpToDest(bt.Task):
    """ Place le mobile en position mobile.ndest et copie la valeur mobile.ndest vers mobile.npos
        lorsque la distance entre mobile.npos et mobile.ndest a été parcourue. """
    def __init__(self, mobile):
        super().__init__()
        self.mobile = mobile
        self.distance_cible = 0
        self.distance_parcourue = 0
        self.distance_restante = 0
        self.current_target = None

    def run(self):
        """
        :return: ``bt.Task.SUCCES`` lorsque distance_restante < 0 sinon ``bt.Task.RUNNING``
        """
        self.UpdatePath()
        if self.mobile.ndest is None:
            return bt.Task.SUCCES

        if self.distance_parcourue <= 0.0:
            position_cible = self.mobile.ndest.box.pos
            self.distance_cible = simulation.simulation.base.Vecteur2D.distsqrt(self.mobile.noeud.box.pos, position_cible) + self.distance_restante
            self.distance_restante = 0.0

        self.distance_parcourue += self.mobile.vit
        self.distance_restante = self.distance_cible - self.distance_parcourue

        if self.distance_restante < 0.0:
            self.distance_parcourue = 0.0
            self.mobile.npos = self.mobile.ndest
            self.mobile.noeud.box.pos = self.mobile.npos.box.pos
            self.mobile.ndest = None
            if self.mobile.path:
                self.mobile.ndest = self.mobile.path.pop()
                return bt.Task.RUNNING
            else:
                return bt.Task.SUCCES
        else:
            return bt.Task.RUNNING

    def UpdatePath(self):
        if self.current_target is not self.mobile.target:
            if self.mobile.target is not None:
                self.current_target = self.mobile.target
                path = simulation.pathfinder.aStar.trouverChemin(self.mobile.npos, self.current_target, self.mobile.masque)
                if path:
                    self.mobile.path = path
                    self.mobile.ndest = self.mobile.path.pop()


class timedJumpToDest(bt.Task):
    """ Place le mobile en position mobile.ndest et copie la valeur mobile.ndest vers mobile.npos
        lorsque la distance entre mobile.npos et mobile.ndest a été parcourue. """
    def __init__(self, mobile):
        super().__init__()
        self.mobile = mobile
        self.depart = True
        self.temps_noeud = self.mobile.vit + self.mobile.accl
        #print(self.temps_noeud)
        self.current_target = None

    def run(self):
        """
        :return: ``bt.Task.SUCCES`` lorsque distance_restante < 0 sinon ``bt.Task.RUNNING``
        """
        self.UpdatePath()
        if self.mobile.ndest is None:
            return bt.Task.SUCCES

        if self.temps_noeud < 0:
            self.temps_noeud = self.mobile.vit + self.mobile.accl if self.depart else self.mobile.vit

        self.temps_noeud -= 1

        if self.temps_noeud < 0:
            self.mobile.npos = self.mobile.ndest
            self.mobile.noeud.box.pos = self.mobile.npos.box.pos
            self.mobile.ndest = None
            self.depart = False
            if self.mobile.path:
                self.mobile.ndest = self.mobile.path.pop()
                return bt.Task.RUNNING
            else:
                return bt.Task.SUCCES
        else:
            return bt.Task.RUNNING

    def UpdatePath(self):
        if self.mobile.target != self.current_target:
            if self.mobile.target is not None:
                self.current_target = self.mobile.target
                path = simulation.pathfinder.aStar.trouverChemin(self.mobile.npos, self.current_target, self.mobile.masque)
                if path:
                    self.depart = True
                    self.mobile.path = path
                    self.mobile.ndest = self.mobile.path.pop()


class moveToDest(bt.Task):
    """ Déplace le mobile de (mobile.vit) mètre(s) en projetant le vecteur velocity
        sur le vecteur (mobile.npos - mobile.noeud)
        Copie la valeur mobile.ndest vers mobile.npos
        lorsque la distance entre mobile.npos et mobile.ndest a été parcourue. """
    def __init__(self, mobile):
        super().__init__()
        self.mobile = mobile
        self.current_target = None

    def run(self):
        """
        :return: ``bt.Task.RUNNING`` lorsque le vecteur projeté est plus petit que (mobile.npos - mobile.noeud) sinon ``bt.Task.SUCCES``
        """
        self.UpdatePath()

        if self.mobile.ndest is None:
            return bt.Task.ECHEC

        position_cible = self.mobile.ndest.box.pos
        cible = simulation.simulation.base.Vecteur2D.sub(position_cible, self.mobile.noeud.box.pos)
        distance = simulation.base.Vecteur2D.distsqrt(self.mobile.noeud.box.pos, position_cible)
        direction = cible[0]/(distance+0.00000001), cible[1]/(distance+0.00000001)

        velocity = direction[0] * self.mobile.vit, direction[1] * self.mobile.vit

        t, projection = simulation.base.Vecteur2D.proj(velocity, cible)
        self.mobile.noeud.box.pos = simulation.base.Vecteur2D.add(self.mobile.noeud.box.pos, projection)
        if 0.0 < t < 1.0:
            return bt.Task.RUNNING
        else:
            self.mobile.npos = self.mobile.ndest
            self.mobile.ndest = None
            if self.mobile.path:
                self.mobile.ndest = self.mobile.path.pop()
                return bt.Task.RUNNING
            else:
                return bt.Task.SUCCES

    def UpdatePath(self):
        if self.current_target is not self.mobile.target:
            self.current_target = self.mobile.target
            path = simulation.pathfinder.aStar.trouverChemin(self.mobile.npos, self.current_target, self.mobile.masque)
            if path:
                self.mobile.path = path
                self.mobile.ndest = self.mobile.path.pop()