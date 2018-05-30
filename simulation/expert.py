"""
Utilitaires pour les systemes experts.
--------------------------------------

Le diagramme suivant montre les principales classes. Notons que `expert.Knowledge` est 
une classe abstraite. Il faut mettre en oeuvre la méthode `_apply` dans une classe 
dérivée et faire un `register`dans une instance de `expert.BaseKnow` afin de pouvoir 
activer l'inférence via la méthode `run`, qui va s'appliquer et enrichir une base de faits 
(instance de `expert.BaseFact`).

.. image::  images/expert.png
    :align: center

Le système expert à base de connaissances est souvent combiné avec le concept de 
`expert.Agent` intelligent. Le diagramme de classe suivant montre l'architecture de base.

.. image::  images/agent.png
    :align: center


"""
from abc import ABCMeta, abstractmethod
from . import base

class BaseKnow(object):
    """ Base de connaissances. """

    def __init__(self):
        """ Init de la base de connaissances."""
        self.k=[] # les connaissances
        self.maxloop=4 # max de loop d'inference
        self.maxloopreached=False # True si on a atteint le max de loop
        self.loopdone=0 # trace du nb de loop done lors de l'inference

    def register(self,know):
        """ Register une connaissance dans la base. 

        :param know: connaissance a enregistrer
        :type know: :class:`expert.Knowledge`
        """
        if isinstance(know,Knowledge): # on a bien une connaissance (derivee de Knowledge)
            self.k.append(know)

    def run(self,bf):
        """ Run le moteur d'inférence. """
        self.maxloopreached=False
        self.loopdone=0
        self.reset() # remet a 0 time_fired de toutes les connaissances
        for i in range(self.maxloop):
            nb_fired=0 # nb connaissance fired
            for know in self.k:
                if know.time_fired==0: # pas encore fired dans ce run
                    if know.run(bf): nb_fired+=1
            print("Debug:",nb_fired)
            if nb_fired==0: break # aucune connaissance s'est applique dans ce tour
        self.loopdone=i+1
        if self.loopdone==self.maxloop and nb_fired>0:
            self.maxloopreached=True

    def reset(self):
        """ Remet a 0 le status de fired pour toute les connaissances de la base. """
        for know in self.k:
            know.time_fired=0


class Knowledge(object, metaclass=ABCMeta):
    """Classe abstraite pour une connaissance du système expert. """

    def __init__(self):
        self.info="Nature non-specifie" # info sur la nature de la connaissance
        self.has_fired=False # status d'execution
        self.time_fired=0

    def run(self,bf):
        """Méthode pour appliquer la connaissance sur une base de faits. Elle appelle 
        la méthode `apply` et gère l'historique des trigger (fired). Notons que ce concept 
        de connaissance est plus général qu'un simple if-then-else. Ça peut-être le 
        résultat d'une analyse statistique, d'une classification, etc. Par convention, 
        si la connaissance provoque un changement à la base de faits, on considère qu'elle a fired.

        :param bf: base de faits
        :type bf: :class:`base.TripleManager`
        :return: True si la connaissance a fired, False sinon
        """
        self.has_fired=False # status d'execution
        self.has_fired = self.apply(bf)
        if self.has_fired: 
            self.time_fired+=1
        return self.has_fired
        
    @abstractmethod
    def apply(self,bf):
        """Méthode abstraite pour appliquer la connaissance sur une base de faits.

        :return: True si la connaissance a fired, False sinon
        """
        return False


class BaseFact(object):
    """ Base de faits. """

    ADDED, COMBINE, KEEPOLD, KEEPNEW = range(4)
    EPS = 0.01

    def __init__(self,strategy=KEEPNEW):
        """ Init de la base de faits."""
        self.wipe() # base de faits neuve
        self.strategy=strategy # strategy de resolution de conflits

    def wipe():
        """ Partir ou repartir avec une base de fait vide. """        
        self.f = base.TripleManager(True) # base de faits

    def addfact(self, anobject, aproperty, avalue, cf=1.0):
        """ Add un fait avec un cf (defaut=1.0, i.e. certain). """
        if self.strategy==BaseFact.KEEPOLD:
            if self.f.getv( (anobject, aproperty) ) is None:
                self.f.add(anobject, aproperty, avalue, cf)
        elif self.strategy==BaseFact.COMBINE:
            if self.f.getv( (anobject, aproperty) ) is None:
                self.f.add(anobject, aproperty, avalue, cf)
            else:
                cfold=self.f.getc( (anobject, aproperty) )
                cfnew=self._combine(cfold,cf)
                self.f.add(anobject, aproperty, avalue, cfnew)
        else: # cas strategy KEEPNEW
            self.f.add(anobject, aproperty, avalue, cf)

    def _combine(self,x,y):
        """ Combine 2 cf comme dans 
        `Mycin <https://en.wikipedia.org/wiki/Mycin>`_. """
        if x>0 and y>0:
            cf = x+y-x*y
        elif x<0 and y<0:
            cf = x+y+x*y
        else:
            z=x+y
            if -BaseFact.EPS<z and z<BaseFact.EPS:
                cf=0.0
            else:
                if x<0: x=-x
                if y<0: y=-y
                if y<x: x=y
                cf=z/(1.0-x)
        return cf


class Agent(object):
    """ Agent intelligent avec méthodes abstraites pour percevoir, comprendre et agir sur 
        l'environnement. L'agent a une mémoire sous la forme d'un blackboard."""

    def __init__(self):
        """ Init de l'agent."""
        self.me = base.Blackboard() # memoire de l'agent

    @abstractmethod
    def percevoir(self):
        """Méthode abstraite pour percevoir l'environnement. Ceci revient souvent à 
           collecter des faits une base de faits en mémoire."""
        pass

    @abstractmethod
    def comprendre(self):
        """Méthode abstraite pour raisonner. Ceci revient souvent à appliquer des 
           connaissances en mémoire sur une base de faits aussi  en mémoire."""
        pass

    @abstractmethod
    def agir(self,bf):
        """Méthode abstraite pour agir sur l'environnement. Ceci revient souvent à 
           analyser une base de faits en mémoire et envoyer des messages d'action."""
        pass

    def run(self):
        """Application successive de percevoir -> comprendre -> agir."""
        self.percevoir()
        self.comprendre()
        self.agir()



