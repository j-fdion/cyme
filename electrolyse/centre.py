"""
Composants et systèmes reliés au procédé d'électrolyse.
-------------------------------------------------------
"""
import re

import math
from kivy.graphics.context_instructions import Color, PushMatrix, Rotate, PopMatrix, Translate
from kivy.graphics.vertex_instructions import Rectangle, Line
from kivy.core.text import Label as CoreLabel

from .. import simulation
from .. import ecs


class Secteur(ecs.Component):
    """Le secteur de production est une entité qui formé d'une liste de cuves, 
       de tâches à faire et d'un pont qui y est affecté. On regrouppe souvent les secteurs 
       en famille. 
    """

    def __init__(self, cuve_debut, allee_debut, nb, famille, nom, num_quart_depart=0):
        """
        :param Cuve cuve_debut: première cuve du secteur
        :param Allee allee_debut: première allée du secteur (peut-être None si pas d'allée)
        :param int nb: nombre de cuve du secteur
        :param str famille: nom de la famille avec ce secteur
        :param str nom: nom du secteur
        :param int num_quart_depart: numéro du quart de départ des opération dans les listes de tâches (0 par défaut)
        """
        self.famille = famille
        self.nom = nom
        self.cuve_debut = cuve_debut # handle sur la premiere cuve du secteur
        self.allee_debut = allee_debut
        self.nbcuve = nb  # nombre de cuves d'un secteur

        if cuve_debut:
            self.cuve_debut = cuve_debut  # handle sur la premiere cuve du secteur
            c = self.cuve_debut.noeud
            c.cuve.secteur = self
            self.noeuds_cuves = [c]
            for i in range(nb - 1):
                c = c.next()
                c.cuve.secteur = self
                self.noeuds_cuves.append(c)
            self.cuve_fin = c.cuve

        if allee_debut:
            self.allee_debut = allee_debut
            a = self.allee_debut.noeud
            a.allee.secteur = self
            self.noeuds_allees = [a]
            for i in range(nb - 1):
                a = a.next()
                a.allee.secteur = self
                self.noeuds_allees.append(a)
            self.allee_fin = a

        self.num_quart = num_quart_depart

        #kanbans est une liste de liste de kanbans, chaque liste représente un quart (ou poste) de travail
        self.kanbans = None
        # pont actuellement affecté aux tâches (kanbans) dans ce secteur 
        self.pont = None
        self.quota_pause = 0

    def set_kanbans(self, kanbans):
        """ Set la liste de listes de kanban (tâches a faire dans ce secteur). 
            A priori, il y a une liste de tâches par quart (poste), avec cycle. 
            Typiquement, on cycle a tous les 2 ou 8 quarts, dépendamment du centre d'électrolyse. 
            C'est le nombre de liste de kanban dans kanbans qui fixe le cycle. """
        self.kanbans = kanbans

    def incr_num_quart(self):
        """ On avance d'une liste de tâche quand on change de quart (poste). """
        if len(self.kanbans) > 0:
            self.num_quart = (self.num_quart + 1) % len(self.kanbans)

    def get_kanbans_for_current_quart(self):
        """ Return la liste de kanban du quart courant. """
        return self.kanbans[self.num_quart]

    def num_quart_max(self):
        """ Nombre de listes de kanban, c'est-à-dire le nombre de postes du cycle. """
        return len(self.kanbans)

    def __repr__(self):
        """ Nom du secteur via repr() """
        return self.nom


class Allee(ecs.Component):
    """ Allee voisine des cuves pour poser les cabarets d'anodes et les bennes. """
    def __init__(self, n):
        self.noeud = n
        self.noeud.allee = self

        self.need_cab_ea = False
        self.need_ben_vide = False

        self.has_cab_megot = False
        self.has_ben_pleine = False

        self.ea = 0
        self.megot = 0
        self.ben = -1

    def is_vide(self):
        if self.ea <= 0 and self.megot <= 0 and self.ben < 0:
            return True
        else:
            return False

    def is_occupee(self):
        if self.ea > 0 or self.megot > 0 or self.ben > -1:
            return True
        else:
            return False


class Cuve(ecs.Component):
    """Aspect cuve électrolytique d'un ``Noeud`` du graphe. Attributs:

         * kA (int): courant sur cette cuve
         * Faraday (float): facteur efficacite electrique en % (fonction du kA)
         * R (float): cte de rendement en kg/(kA*24h)
         * nbanode: nombre d'anodes dans la cuve
         * cycle: cycle anodique en jours (float)
         * na (float): nombre d'anodes a changer selon le cycle (variable d'état)
         * metal (float): quantité de métal liquide siphonnable en kg (variable d'état)
    """

    def __init__(self, n, nbanode, cycle=600, ka=400):
        """:param n: on garde un handle vers le composant noeud frère
        :type n: :class:`Noeud`
        :param int nanode: nombre d'anodes (ea) dans une cuve
        :param int cycle: cycle anodique en heures (defaut: 600h, i.e. 25j)
        :param int ka: courant electrique en ka (defaut: 400kA)
        """
        self.noeud=n # handle sur le noeud
        self.noeud.cuve=self # handle du noeud vers sa cuve
        self.nbanode=nbanode # nombre d'anodes dans la cuve
        self.metal=3380.0 # kg de metal siphonnable
        self.megot=0 # nb de ea a changer (megots)
        self.R=8.0534 # cte standard de production en kg/(kA*24h) (voir doc)
        self.set_kA(ka) # set le courant et le rendement en kA
        self.set_cycle(cycle) # set le cycle anodique
        self.nch=1 # nb d'anodes a changer au prochain changement d'anodes
        self.nsi=1 # 1 s'il y a du metal a siphonner, 0 sinon (NB: dans le futur ce sera le nb de kg)

    def set_cycle(self,cycle):
        """ Set le cycle anodique. """
        self.cycle = cycle  # cycle de changement des anodes en heures
        # facteur production de megots par 60 secondes
        self.factMegot = self.nbanode / (self.cycle * 60.0)

    def set_kA(self, ka):
        """Set la valeur du courant et du rendement Faraday (typiquement entre 90% et 97%)."""
        self.kA = ka
        self.Faraday = 0.93  # efficacite electrique en % (depend generalement du kA)
        # facteur production de metal par 60 secondes
        self.factMetal = 60.0 * self.R * self.Faraday * self.kA / 86400.0

    def productionMetal(self, periode):
        """Calcul la quantité de métal total produit par la cuve en ``periode`` minutes."""
        return self.factMetal * periode

    def productionMegot(self, periode):
        """Calcul la quantité de mégots total produit par la cuve en ``periode`` minutes."""
        return self.factMegot * periode

    def update(self):
        """Update de l'etat de la cuve apres 60 secondes."""
        self.metal += self.factMetal
        self.megot += self.factMegot
        if self.megot >= 1.0:
            self.nch += 1
            self.megot -= 1


class RenderCuve(ecs.System):
    """Systeme pour le rendering des cuves."""

    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas

    def init(self):
        pass

    def reset(self):
        pass

    def update(self, dt):
        with self.canvas:
            for entity, cuve in self.entity_manager.pairs_for_type(Cuve):
                box = self.entity_manager.component_for_entity(entity, simulation.graphe.Box)
                # draw rectangle with texture
                Color(box.color[0], box.color[1], box.color[2], box.alpha)
                Rectangle(pos=box.pos, size=box.size)
                Color(box.contour_color[0], box.contour_color[1], box.contour_color[2], box.alpha)
                Line(rectangle=box.pos + box.size)
                # texte
                #PushMatrix()
                #my_label=CoreLabel(text=str(cuve.nch), font_size=10) # affichage du nb d'anodes a changer
                #my_label=CoreLabel(text=" {0:.0f}  {1:.1f}".format(cuve.metal,cuve.megot), font_size=10) # affichage du metal et du nb d'anode
                #my_label.refresh() # force label to draw itself
                #x_texture=my_label.texture # use the label texture
                #Translate(float(box.ptxt[0]-3), float(box.ptxt[1]), 0)
                #Rotate(90, 0, 0, 1)
                #Rectangle(size=x_texture.size, pos=(0,0), texture=x_texture)
                #PopMatrix()


class RenderAllee(ecs.System):
    """Systeme pour le rendering des cuves."""

    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas

    def init(self):
        pass

    def reset(self):
        pass

    def update(self, dt):
        with self.canvas:
            for entity, allee in self.entity_manager.pairs_for_type(Allee):
                box = self.entity_manager.component_for_entity(entity, simulation.graphe.Box)
                # draw rectangle with texture

                Color(box.color[0], box.color[1], box.color[2], box.alpha)
                if allee.need_cab_ea:
                    Color(0,1,0, box.alpha)
                if allee.need_ben_vide:
                    Color(0, 0, 1, box.alpha)
                if allee.has_cab_megot:
                    Color(0.2, 1, 0.2, box.alpha)
                if allee.has_ben_pleine:
                    Color(0.2, 0.2, 1, box.alpha)

                Rectangle(pos=box.pos, size=box.size)

                Color(0, 0, 0)  # toujours un coutour noir

                Line(rectangle=box.pos + box.size)

                #PushMatrix()
                #my_label = CoreLabel(text=str(allee.secteur.nom), font_size=12)
                ## my_label=CoreLabel(text=" {0:.0f}  {1:.1f}".format(cuve.metal,cuve.megot), font_size=10)
                #my_label.refresh()  # force label to draw itself
                #x_texture = my_label.texture  # use the label texture
                #Translate(float(box.ptxt[0]), float(box.ptxt[1])+5,0)
                #Rotate(90, 0, 0, 1)
                #Rectangle(size=x_texture.size, pos=(0, 0), texture=x_texture)
                #PopMatrix()

