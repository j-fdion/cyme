"""
Composants et systèmes reliés aux machines
------------------------------------------

Le concept de :class:`Machine` est un composant associé à un :class:`cyme.simulation.graphe.Noeud`, capable de déplacer du matériel entre des sources et des destinations. Le behavior tree ci-dessous montre l'IA de la machine. Essentiellement, on boucle sur les étapes:

  * si la machine opère (état Actif)
  * si toutes les contraintes d'entrée sont satisfaites
  * laisser passer un temps de réalisation (Delay)
  * si toutes les contraintes de déplacement du matériel sont satisfaites
  * déplacer le matériel

Avec un choix judicieux des contraintes d'entrée et de sortie, cette abstraction d'une machine permet de représenter le flux de systèmes relativement complexes. De plus, elle peut servir de base pour créer des machines plus complexes.

.. image::  images/bt_machine.png
   :height: 255px
   :width: 600px
   :scale: 100 %
   :align: center

Les sources et destinations pour le matériel sont des entités avec un composants :class:`Accumulateur` 
ou sa version spécialisée :class:`Transit`. L'accumulateur est associé à une :class:`cyme.simulation.graphe.Arete` 
et représente le concept de matériel accumulé. En pratique, on s'en sert pour représenter un réservoir, 
un entrepôt ou tout autre chose qui sert à stocker du matériel. A priori, le matériel qui y est mis est 
immédiatement disponible. La spécialisation :class:`Transit` ajoute une notion de temps de transit du 
matériel. Elle sert à représenter des convoyeurs ou tout autre élément de stockage où le matériel doit 
séjourner un certain temps avant d'être disponible.

Dans un modèle basé sur :class:`Machine` et :class:`Accumulateur`, le matériel est seulement dans les 
accumulateurs et seul les machines déplacent le matériel.

Le décorateur :class:`cyme.bt.decorator.RepeatUntilSucces` permet de s'assurer que toutes les conditions 
sont validées avant de réaliser la tâche. Notons qu'on suppose implicitement que lorsque la liste de conditions 
est satisfaite, tous les éléments de tâche peuvent être réalisés sans autres conditions. 
Si on n'exige pas que toutes les conditions soient satisfaites pour poursuivre, on peut remplacer 
le noeud :class:`cyme.bt.nodetypes.Sequence` qui est juste devant par correspondant par un noeud 
:class:`cyme.bt.nodetypes.Selector` qui poursuit dès qu'une des conditions est satisfaite. 
Cependant, ceci pose des problèmes car en réalité il faut généralement cycler équitablement entre les 
entrées. Ces fonctionalités ne sont donc pas dans la machine de base.

"""

from kivy.graphics.context_instructions import Color
from kivy.graphics.vertex_instructions import Rectangle, Line
from kivy.core.text import Label as CoreLabel

from .. import ecs, bt, simulation
from . import bt_machine


class AiguillageY(ecs.Component):
    """ Un aiguillage en Y est essentiellement un deplacement instantanné de une 
        unité de matériel par cycle de chacun des accumulateurs en entrée vers la sortie. 
        À condition qu'il y ait du matériel en entrée et de la place en sortie. 
        La simplicité de l'aiguillage ne nécessite pas de BT.
    """

    def __init__(self, n, nom):
        """:param n: :class:`cyme.simulation.graphe.Noeud` noeud auquel est associé l'aiguillage
        :param nom: nom de l'aiguillage pour l'affichage
        """
        # parametres
        self.noeud = n  # handle sur le noeud
        self.nom = nom  # nom de la machine
        self.x = 0  # var d'etat pour quantite traitee en entree
        self.xout = 0 # var d'etat pour quantite traitee en sortie
        self.actif = True  # opere normalement si True, sinon en arret

    def update(self):
        """ Update. """
        # on suppose que tout va sur le 0
        accum_sortie = self.noeud.oua[0].accumulateur if self.noeud.oua else None  
        for idx in range(len(self.noeud.ina)):
            accum = self.noeud.ina[idx].accumulateur
            if accum_sortie:
                if accum.dispo()>0 and not accum_sortie.full():
                    accum.rm()
                    accum_sortie.add()
                    self.x+=1
                    self.xout+=1
            else:
                if accum.dispo() > 0:
                    accum.rm()
                    self.x += 1


class Machine(ecs.Component):
    """ Une machine de base pour le flux de matériel discret. Bien qu'on update en temps discret,  
        le tcyle peut être un nombre réel: un mécanisme tiens compte des fractions. 
        Cette version générique de machine permet de modifier la liste des pre et post-conditions. 
        Dans ce cas, il faut forcer la reconstruction du BT via :meth:`setup_behavior`. 
        Au niveau de la tâche finale, tous les accumulateurs en entrée sont débités selon qin et 
        le matériel est mis à la sortie selon qout. 
    """

    def __init__(self, n, nom, tcycle, qin, qout):
        """:param n: :class:`cyme.simulation.graphe.Noeud` noeud auquel est associé la machine
        :param nom: nom de la machine pour l'affichage
        :param tcycle: temps de traitement du matériel par la machine (int ou float)
        :param qin: liste d'entiers de la quantité de matériel requis sur les accumulateurs en entrée
        :param qout: liste d'entiers de la quantité de matériel produit sur les accumulateurs en sortie
        """
        # parametres
        self.noeud = n  # handle sur le noeud
        self.nom = nom  # nom de la machine
        self.x = 0  # var d'etat pour quantite traitee en entree
        self.xout = 0 # var d'etat pour quantite traitee en sortie
        self.tcycle = tcycle  # temps de cycle de la machine (int ou float)
        self.qin = qin # liste de quantite de materiel prerequis en entree 
        self.qin_total_par_cycle = sum(qin)
        self.qout = qout # liste de quantite de materiel produit en sortie
        self.qout_total_par_cycle = sum(qout)
        self.actif = True  # opere normalement si True, sinon en arret
        # variables internes
        self.travail_perdu=0 # si une condition d'entree n'est plus valide lors de la sortie, ou a perdu du temps 
        self.bb = simulation.base.Blackboard()  # un blackboard (memoire)
        self.precondition = [] # liste des preconditions (entree)
        self.postcondition = [] # liste des postconditions (valides les sorties)
        self.pretache = []
        self.posttache = []
        self.setup_precondition()  # on construit les preconditions
        self.setup_postcondition()  # on construit les postconditions
        self.setup_behavior()  # on construit l'IA

    def setup_precondition(self):
        """ On construit la liste des preconditions. """
        for idx in range(len(self.noeud.ina)):
            accum = self.noeud.ina[idx].accumulateur # handle sur le composant accumulateur
            self.precondition.append(bt_machine.entreeTest_i(self,accum,self.qin[idx]))

    def setup_postcondition(self):
        """ On construit la liste des postconditions. """
        for idx in range(len(self.noeud.oua)):
            accum = self.noeud.oua[idx].accumulateur # handle sur le composant accumulateur
            self.postcondition.append(bt_machine.sortieTest_i(self,accum,self.qout[idx]))

    def setup_behavior(self):
        """ On construit ou reconstruit le BT de la machine. """
        self.root = self.behavior_flux() # construction du BT

    def update_bb(self):
        """ Update des données du blackboard. """
        pass

    def behavior_flux(self):
        aroot = bt.decorator.Actif(self) # test d'activite accroche a la racine
        # Sequence *
        topnode = bt.SequenceStar() # connecte au decorateur du test d'activite
        aroot.add_child(topnode) # accroche topnode a la racine
        ### BLOC ENTREE
        #   Sequence 
        sequenceEntree = bt.Sequence()
        topnode.add_child(sequenceEntree)
        #     Repeat Until Success
        repeatEntree = bt.decorator.RepeatUntilSucces()
        sequenceEntree.add_child(repeatEntree)
        #       Sequence ou Selector des pre-conditions
        node_pre = bt.Sequence() # remplacer par un bt.Selector() le premier qui a dispo
        repeatEntree.add_child(node_pre)
        #         Pre-conditions
        for test in self.precondition: node_pre.add_child(test)
        #     Tache entree
        sequenceEntree.add_child(bt_machine.preTache(self)) # tache
        for test in self.pretache: sequenceEntree.add_child(test)
        ### BLOC CENTRAL
        #   Delay
        delay = bt.decorator.Delay(self.tcycle)
        self.bb.delay = delay
        topnode.add_child(delay)
        delay.add_child(bt_machine.machineTache(self)) # tache
        ### BLOC SORTIE
        #   Sequence 
        sequenceSortie = bt.Sequence()
        topnode.add_child(sequenceSortie)
        #     Repeat Until Success
        repeatSortie = bt.decorator.RepeatUntilSucces()
        sequenceSortie.add_child(repeatSortie)
        #       Sequence des post-conditions
        node_post = bt.Sequence()
        repeatSortie.add_child(node_post)
        #         Post-conditions
        for test in self.postcondition: node_post.add_child(test)
        #     Tache sortie
        sequenceSortie.add_child(bt_machine.postTache(self)) # tache
        for test in self.posttache: sequenceSortie.add_child(test)

        return aroot

    def update(self):
        """ Update des données du blackboard et run le BT (un cycle). """
        self.update_bb()
        self.root.run()


class Accumulateur(ecs.Component):
    infini = 999999  # pour wmax sans limite

    def __init__(self, a, w, wmax):
        self.arete = a
        self.arete.accumulateur = self  # handle de l'arete vers l'accumulateur
        self._w = w
        self._wmax = wmax

    def get(self):
        return self._w

    def dispo(self):
        return self._w

    def full(self, k=1):
        """ True si l'ajout de k fait deborder la capacite. """
        return self._w + k > self._wmax

    def empty(self, k=1):
        return self._w - k < 0

    def add(self, k=1):
        if not self.full(k):
            self._w += k
            return True
        else:
            return False

    def rm(self, k=1):
        if not self.empty(k):
            self._w -= k
            return True
        else:
            return False

    def getmax(self):
        return self._wmax

    def update(self):
        pass


class Transit(Accumulateur):
    infini = 999999  # pour wmax sans limite

    def __init__(self, a, w, wmax, transit):
        super().__init__(a, w, wmax)
        self._transit = transit
        self._fifo = []
        self._fifo = [self._transit] * self._w  # initialisation

    def get(self):
        return len(self._fifo)

    def dispo(self):  # partie du nombre actuellement disponible
        n = 0
        for z in self._fifo:
            if z >= self._transit: n += 1
        return n

    def full(self, k=1):
        """ True si l'ajout de k fait deborder la capacite. """
        return len(self._fifo) + k > self._wmax

    def empty(self, k=1):
        return len(self._fifo) - k < 0

    def add(self, k=1):
        if not self.full(k):
            for _ in range(k): self._fifo.append(0)
            return True
        else:
            return False

    def rm(self, k=1):
        if not self.empty(k):
            for _ in range(k): self._fifo.pop(0)
            return True
        else:
            return False

    def add_list(self, t, l):
        """ Insere la liste l devant le temps t. """
        if not self.full(len(l)):
            idx = 0
            for i in range(len(l)):
                if t <= self._fifo[i]:
                    idx = i
                    break
            if t <= self._fifo[idx]:
                self._fifo[idx:idx] = l
            else:
                self._fifo += l
            return True
        else:
            return False

    def dispo_dans_au_plus(self, t):
        """ Nb d'items dispo maintenant et aussi dans au plus t. """
        n = 0
        for z in self._fifo:
            if z + t >= self._transit: n += 1
        return n

    def add_at(self, t, k=1):
        """ Si possible, on ajoute k items de valeur t devant l'item de valeur t (au pire, a la fin). """
        if not self.full(k):
            i = 0
            while i < len(self._fifo):
                if self._fifo[i] > t:
                    i += 1
                else:
                    break
            if i >= len(self._fifo):
                for a in range(k):
                    self._fifo.append(0)
            else:
                x = [t] * k
                self._fifo[i:i] = x
            return True
        else:
            return False

    def rm_at(self, t, k=1):
        """ Si possible, on retire k items de valeur t et debordant sur ceux devant, i.e. avec t plus grand. """
        if not self.empty(k):
            i = 0
            while i < len(self._fifo):
                if self._fifo[i] >= t:
                    i += 1
                else:
                    break
            if i - k >= 0:
                del self._fifo[i - k:i]
                return True
        else:
            return False

    def show(self):
        print(self._fifo)

    def update(self):
        self._fifo = [z + 1 for z in self._fifo]


class RenderMachine(ecs.System):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas

    def init(self):
        pass

    def reset(self):
        pass

    def update(self, dt):
        with self.canvas:
            for entity, m in self.entity_manager.pairs_for_type(Machine):
                # Couleur du texte rgba
                if m.actif:
                    Color(0, 1, 0)
                else:
                    Color(1, 1, 0)
                if not float(m.x).is_integer():
                    s = str(round(m.x,3))
                else:
                    s = "{0}/{1}".format(m.x, m.xout)
                my_label = CoreLabel(text=m.nom + '\n' + s, font_size=14)
                # the label is usually not drawn until needed, so force it to draw.
                my_label.refresh()
                # Now access the texture of the label and use it wherever
                x_texture = my_label.texture
                b = self.entity_manager.component_for_entity(entity, simulation.graphe.Box)
                Rectangle(size=x_texture.size, pos=b.ptxt, texture=x_texture)

class RenderAiguillageY(ecs.System):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas

    def init(self):
        pass

    def reset(self):
        pass

    def update(self, dt):
        with self.canvas:
            for entity, m in self.entity_manager.pairs_for_type(AiguillageY):
                # Couleur du texte rgba
                if m.actif:
                    Color(0, 1, 0)
                else:
                    Color(1, 1, 0)
                if not float(m.x).is_integer():
                    s = str(round(m.x,3))
                else:
                    s = "{0}/{1}".format(m.x, m.xout)
                my_label = CoreLabel(text=m.nom + '\n' + s, font_size=14)
                # the label is usually not drawn until needed, so force it to draw.
                my_label.refresh()
                # Now access the texture of the label and use it wherever
                x_texture = my_label.texture
                b = self.entity_manager.component_for_entity(entity, simulation.graphe.Box)
                Rectangle(size=x_texture.size, pos=b.ptxt, texture=x_texture)



class RenderAccumulateur(ecs.System):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas

    def init(self):
        pass

    def reset(self):
        pass

    def update(self, dt):
        with self.canvas:
            for entity, a in self.entity_manager.pairs_for_type(Accumulateur):
                # Couleur du texte rgba
                if a.full():
                    Color(0.7, 0, 0)  # rouge c'est plein
                elif a.empty():
                    Color(0, 1, 1)  # cyan c'est vide
                elif a.get() < a.dispo():  # tout n'est pas dispo (a cause de transit)
                    Color(1, 1, 0)  # jaune c'est partiellement dispo
                else:
                    Color(0, 1, 0)  # vert tout est dispo
                if not float(a.get()).is_integer():
                    s = str(round(a.get(),3))
                    if a.getmax() != Accumulateur.infini:
                        s += "/" + str(round(a.getmax(),3))
                else:
                    s = str(a.get())
                    if a.getmax() != Accumulateur.infini:
                        s += "/" + str(a.getmax())

                my_label = CoreLabel(text=s, font_size=14)
                # the label is usually not drawn until needed, so force it to draw.
                my_label.refresh()
                # Now access the texture of the label and use it wherever
                x_texture = my_label.texture
                li = self.entity_manager.component_for_entity(entity, simulation.graphe.Ligne)
                Rectangle(size=x_texture.size, pos=li.ptxt, texture=x_texture)


class RenderTransit(ecs.System):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas

    def init(self):
        pass

    def reset(self):
        pass

    def update(self, dt):
        with self.canvas:
            for entity, a in self.entity_manager.pairs_for_type(Transit):
                # Couleur du texte rgba
                if a.full():
                    Color(0.7, 0, 0)  # rouge c'est plein
                elif a.empty():
                    Color(0, 1, 1)  # cyan c'est vide
                elif a.get() < a.dispo():  # tout n'est pas dispo (a cause de transit)
                    Color(1, 1, 0)  # jaune c'est partiellement dispo
                else:
                    Color(0, 1, 0)  # vert tout est dispo
                s = str(a.get())
                if a.getmax() != Transit.infini:
                    s += "/" + str(a.getmax())
                my_label = CoreLabel(text=s, font_size=14)
                # the label is usually not drawn until needed, so force it to draw.
                my_label.refresh()
                # Now access the texture of the label and use it wherever
                x_texture = my_label.texture
                li = self.entity_manager.component_for_entity(entity, simulation.graphe.Ligne)
                Rectangle(size=x_texture.size, pos=li.ptxt, texture=x_texture)


