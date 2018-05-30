"""
Les types de noeuds génériques pour les behavior tree.
------------------------------------------------------
"""
from abc import ABCMeta, abstractmethod


class Task(object, metaclass=ABCMeta):
    """Classe abstraite de base pour les noeuds du behavior tree."""
    ECHEC, SUCCES, RUNNING=range(3)  # compatibilite: False est un ECHEC et True est un SUCCES

    def __init__(self):
        self._children=[]
        self.index=0

    @abstractmethod
    def run(self):
        """Méthode abstraite pour l'exécution et la propagation d'un tick."""
        return

    def add_child(self, c):
        """Ajoute un child au noeud."""
        self._children.append(c)

    def __str__(self, level=0):
        ret = "\t" * level + repr(self.__class__.__name__) + "\n"
        for child in self._children:
            ret += child.__str__(level + 1)
        return ret

class Decorator(Task):
    """Interface pour un noeud decorator."""
    __metaclass__=ABCMeta

    def __init__(self):
        super().__init__()

    def add_child(self, c):
        """Ajoute un child au noeud, mais seulement s'il n'y en a pas (force l'unicité)."""
        if len(self._children)<1:
            super(Decorator, self).add_child(c)


class Selector(Task):
    """Classe concrète pour un noeud selector """

    def __init__(self):
        super().__init__()

    def run(self):
        """Méthode concrète pour la propagation du tick."""
        for i in range(self.index, len(self._children)):
            status=self._children[i].run()
            if status==Task.SUCCES:
                return Task.SUCCES
            elif status==Task.RUNNING:
                return Task.RUNNING
        return Task.ECHEC

    def add_child(self, c):
        """Ajoute un child au noeud."""
        super(Selector, self).add_child(c)


class SelectorStar(Task):
    """Classe concrète pour un noeud selector star."""

    def __init__(self):
        super().__init__()

    def run(self):
        """Methode concrète pour la propagation du tick."""
        for i in range(self.index, len(self._children)):
            status=self._children[i].run()
            if status==Task.SUCCES:
                self.index=0
                return Task.SUCCES
            elif status==Task.RUNNING:
                self.index=i
                return Task.RUNNING
        self.index=0
        return Task.ECHEC

    def add_child(self, c):
        """Ajoute un child au noeud."""
        super(SelectorStar, self).add_child(c)


class Sequence(Task):
    """Classe concrète pour un noeud sequence."""

    def __init__(self):
        super().__init__()

    def run(self):
        """Méthode concrète pour la propagation du tick."""
        for i in range(self.index, len(self._children)):
            status=self._children[i].run()
            if status==Task.ECHEC:
                return Task.ECHEC
            elif status==Task.RUNNING:
                return Task.RUNNING
        return Task.SUCCES

    def add_child(self, c):
        """Ajoute un child au noeud."""
        super().add_child(c)


class SequenceStar(Task):
    """Classe concrète pour un noeud sequence star."""

    def __init__(self):
        super().__init__()

    def run(self):
        """Méthode concrète pour la propagation du tick."""
        for i in range(self.index, len(self._children)):
            status=self._children[i].run()
            if status==Task.ECHEC:
                self.index=0
                return Task.ECHEC
            elif status==Task.RUNNING:
                self.index=i
                return Task.RUNNING
        self.index=0
        return Task.SUCCES

    def add_child(self, c):
        """Ajoute un child au noeud."""
        super().add_child(c)

class Parallel(Task):
    """Classe concrète pour un noeud parallel"""

    def __init__(self):
        super().__init__()

    def run(self):
        """Méthode concrète pour la propagation du tick."""
        succes = 0
        for i in range(self.index, len(self._children)):
            status=self._children[i].run()
            if status==Task.SUCCES or status==Task.RUNNING:
                succes += 1

        if succes > 0:
            return Task.SUCCES
        else:
            return Task.ECHEC

    def add_child(self, c):
        """Ajoute un child au noeud."""
        super().add_child(c)