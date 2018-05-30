"""
Behavior tree des ponts.
------------------------
"""

from .. import bt
from .. import simulation

class MoveToTarget(bt.Task):
    """ Fait bouger le pont vers sa cible, gérer par le composant mobile
    """
    def __init__(self, pont, queue):
        super().__init__()
        self.pont = pont
        self.queue_name = queue

    def run(self):
        """
        :return: ``bt.Task.SUCCES`` si le pont est positionné sur la cible
        """
        if self.pont.secteur is None:
            return bt.Task.ECHEC

        target = getattr(self.pont, self.queue_name)[0].get_current_target(self.pont.secteur)
        #if self.pont.mobile.target != target:
        self.pont.mobile.target = target
        target.box.color = simulation.base.Palette.RED1.to_float()
        value = bt.Task.SUCCES if self.pont.mobile.target == self.pont.mobile.npos else bt.Task.ECHEC
        #if self.pont.nom == "M4":
            #print(self.pont, "MoveToTarget", "SUCCESS" if value == 1 else "ECHEC")
            #self.pont.mobile.target.box.color = (1,0.5,0)
            #self.pont.mobile.npos.box.color = (1,0.5,0)
            #path = simulation.pathfinder.aStar.construireChemin(self.pont.mobile.npos,self.pont.mobile.target)
            #for p in path:
            #    p.box.color = (0,1,0)

        if value == bt.Task.SUCCES:
            target.box.contour_color = simulation.base.Palette.BLACK.to_float()
        return value

class IsQueueEmpty(bt.Task):
    """ Vérifie si la file de pauses est vide
    """
    def __init__(self, pont, queue):
        super().__init__()
        self.pont = pont
        self.queue_name = queue

    def run(self):
        """
        :return: ``bt.Task.SUCCES`` si la file est vide
        """

        value = bt.Task.SUCCES if len(getattr(self.pont, self.queue_name)) == 0 else bt.Task.ECHEC
        ##print(self.__class__, "SUCCESS" if value == 1 else "ECHEC")

        return value

class IsLocked(bt.Task):
    """ Vérifie si la file de pauses est vide
    """
    def __init__(self, pont):
        super().__init__()
        self.pont = pont

    def run(self):
        """
        :return: ``bt.Task.SUCCES`` si la file est vide
        """

        value = bt.Task.SUCCES if self.pont.kanbans_lock else bt.Task.ECHEC
        ##print(self.__class__, "SUCCESS" if value == 1 else "ECHEC")

        return value

class IsSecteurOccupied(bt.Task):
    """ Vérifie si la file de taches du pont du secteur est vide
    """
    def __init__(self, pont):
        super().__init__()
        pass

class Precondition(bt.Task):
    """ Run la precondition liée au type d'opération du kanban
    """

    def __init__(self, pont, queue):
        super().__init__()
        self.pont = pont
        self.queue_name = queue

    def run(self):
        kanban = getattr(self.pont, self.queue_name)[0]
        value = bt.Task.SUCCES if kanban.operation.precondition(self.pont) else bt.Task.ECHEC
        ##print(self.__class__, "SUCCESS" if value == 1 else "ECHEC")

        return value

class Pretache(bt.Task):
    """ Run la precondition liée au type d'opération du kanban
    """
    def __init__(self, pont, queue):
        super().__init__()
        self.pont = pont
        self.queue_name = queue

    def run(self):
        kanban = getattr(self.pont, self.queue_name)[0]
        value = bt.Task.SUCCES if kanban.operation.pretache(self.pont) else bt.Task.ECHEC
        return value


class Tache(bt.Task):
    """ Run la precondition liée au type d'opération du kanban
    """

    def __init__(self, pont, queue):
        super().__init__()
        self.pont = pont
        self.queue_name = queue
        self._delay = -1
        self.delay = -1
        self.kanban = None

    def set_delay(self, delay):
        self._delay = delay
        self.delay = delay

    def run(self):
        """ Run la tache liée au type d'opération du kanban

        :return: ``Task.RUNNING`` tant que delay non atteint, sinon le \
        status de la tache et on reset le delay si celui-ci est autre que ``Task.RUNNING``
        """
        if len(getattr(self.pont, self.queue_name)) > 0:
            kanban = getattr(self.pont, self.queue_name)[0]
            if self.kanban != kanban:
                self.kanban = kanban
                self.set_delay(kanban.operation.get_duree(self.pont))

            if self.delay > 1:
                self.delay -= 1
                self.kanban.temps_restant = self.delay
                return bt.Task.RUNNING
            else:
                status = bt.Task.SUCCES if self.kanban.operation.tache(self.kanban) else bt.Task.ECHEC
                if status == bt.Task.SUCCES:
                    self.delay += self._delay - 1
                    ##print("TACHE", "SUCCES")
                    return bt.Task.SUCCES
                elif status == bt.Task.RUNNING:
                    ##print("TACHE", "RUNNING")
                    return bt.Task.RUNNING
                else:
                    ##print("TACHE", "ECHEC")
                    self.delay += self._delay - 1
                    return bt.Task.ECHEC
        else:
            print("ECHEC", self.pont, self.queue_name,getattr(self.pont, self.queue_name))
            return bt.Task.ECHEC


class Postcondition(bt.Task):
    """ Run la precondition liée au type d'opération du kanban
    """

    def __init__(self, pont, queue):
        super().__init__()
        self.pont = pont
        self.queue_name = queue

    def run(self):
        kanban = getattr(self.pont, self.queue_name)[0]
        value = bt.Task.SUCCES if kanban.operation.precondition(self.pont) else bt.Task.ECHEC
        ##print(self.__class__, "SUCCESS" if value == 1 else "ECHEC")

        return value


class Posttache(bt.Task):
    """ Run la precondition liée au type d'opération du kanban
    """

    def __init__(self, pont, queue):
        super().__init__()
        self.pont = pont
        self.queue_name = queue

    def run(self):
        kanban = getattr(self.pont, self.queue_name)[0]
        if kanban.operation.posttache(self.pont) and kanban.is_completed():
            getattr(self.pont, self.queue_name).popleft()
            return bt.Task.SUCCES
        else:
            return bt.Task.ECHEC