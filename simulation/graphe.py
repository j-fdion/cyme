"""
Composants et systèmes reliés au graphe du modèle.
--------------------------------------------------
"""

from kivy.graphics.context_instructions import Color, PushMatrix, Rotate, PopMatrix, Translate
from kivy.graphics.vertex_instructions import Rectangle, Line
from pprint import pprint

from .. import ecs

class Ligne(ecs.Component):
    """Une ligne simple entre 2 points en pixels. Une ``Ligne`` est associée aux ``Arete``
    que l'on veut rendre visible (rendering), on a donc pas besoin de flag de visibilité."""
    def __init__(self, ends):
        """:param ends: tuple formé des coordonnées des extrémités.
        """
        self.setEnds(ends)
        self.sorte=0 # sorte de ligne (voir Res)
        self.width=1

    def setEnds(self, ends):
        """Toujours utiliser cette méthode pour définir les extrémités.

        :param ends: tuple formé des coordonnées des extrémités.
        """
        self.ends=ends
        self.ptxt=((ends[0]+ends[2])//2+4, (ends[1]+ends[3])//2+4)


class RenderLigne(ecs.System):
    def __init__(self, canvas,couleurs):
        super().__init__()
        self.canvas=canvas
        self.couleurs=couleurs

    def init(self):
        pass

    def reset(self):
        pass

    def update(self, dt):
        with self.canvas:
            for entity, li in self.entity_manager.pairs_for_type(Ligne):
                Color(*self.couleurs[li.sorte])
                Line(points=li.ends, width=li.width)


class Box(ecs.Component):
    """``Box`` sert deux fonctions: définir la structure du modèle qu'on load via
    un fichier csv et pour le rendering des ``Noeud``. On peut limiter la
    visibilité via un flag). La couleur et la texture sont reconfiguration et 
    servent essentiellement au rendering lors d'une simulation. """
    def __init__(self, pos, size):
        """:param pos: couple formé des coordonnées du coins inférieurs gauche.
        :param size: couple formé des dimensions dx et dy.
        """
        self.pos=pos
        self.size=size
        self.cent=(self.pos[0]+self.size[0]//2, self.pos[1]+self.size[1]//2)
        self.ptxt=(self.pos[0]+4, self.pos[1]+4)
        self.visible=True
        self.avecTexture=True
        self.sorte=1 # sorte de box (voir Res)
        self.alpha = 1
        self._color = (1,1,1)
        self._contour_color = (0,0,0)
        self.custom_draw = False

    def m(self, value):
        print(value)

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, value):
        self._color = value
        #self.m(value)

    @property
    def contour_color(self):
        return self._contour_color

    @contour_color.setter
    def contour_color(self, value):
        self._contour_color = value
        #self.m(value)

class PprintBox(ecs.System):
    def __init__(self):
        super().__init__()

    def init(self):
        pass

    def reset(self):
        pass

    def update(self, dt):
        for entity, box in self.entity_manager.pairs_for_type(Box):
            print("component box de: ", entity.name())
            pprint(vars(box))


class RenderBox(ecs.System):
    """Systeme pour le rendering des box."""
    def __init__(self, canvas,couleurs,textures):
        super().__init__()
        self.canvas=canvas
        self.couleurs=couleurs
        self.textures=textures
        self.box = []
        self.custom_draw = []

    def init(self):
        for entity, box in self.entity_manager.pairs_for_type(Box):
            if box.custom_draw:
                self.custom_draw.append(box)
            else:
                box.color = self.couleurs[box.sorte]
                self.box.append(box)

    def reset(self):
        pass

    def update(self, dt):
        with self.canvas:
            for box in self.box:
                Color(box.color[0],box.color[1],box.color[2],box.alpha)
                Rectangle(source=self.textures[box.sorte], pos=box.pos, size=box.size)


class Noeud(ecs.Component):
    """L'un des deux éléments structurels du graphe, l'autre est ``Arete``. 
    Le coloriage sert d'aide à l'élaboration du graphe et éventuellement 
    dans la logique (IA) via le concept de sous graphe. En effet, il permet 
    de caracteriser 3 niveaux de sous-graphes: sous graphes (SG), 
    sous-sous graphes (SSG) et sous-sous-sous graphes (SSSG):

      * SG: même coloris sans égard au facteur alpha
      * SSG: même coloris et même 4 premiers bits du facteur alpha
      * SSSG: même coloris et même facteur alpha

    Notons que ces notions sont "emboitées" l'une dans l'autre comme pour des 
    sous-ensembles, c-à-d que si inSSSG est vrai, alors inSSG et inSG sont aussi vrai.
    """
    def __init__(self, entity):
        """:param entity: on garde un handle vers l'entité père
        :type entity: :class:`ecs.models.Entity`
        """
        self.entity=entity
        self.box=None # handle sur le box pour le rendering
        self.ina=[]
        self.oua=[]
        self.voisins = []
        self.coloris = 0xFFFFFFFF # coloris par defaut est blanc opaque
        self.bloque=False

    def next(self,sens_aval=True):
        """ Prochain ``Noeud`` dans le sens aval (oua) ou amont (ina), avec validation."""
        if sens_aval: return self.oua[0].to if self.oua else None
        else: return self.ina[0].fr if self.ina else None

    def calculerVoisins(self):
        """ Construit la liste des ``Noeud`` du voisinage."""
        if not self.voisins:
            for a in self.oua:
                self.voisins.append(a.to)
            for a in self.ina:
                self.voisins.append(a.fr)

    def inSG(self,col):
        """Retourne vrai si dans le sous-graphe du coloris col, sans tenir compte de l'opacite."""
        return self.coloris>>8 == col>>8

    def inSSG(self,col):
        """Retourne vrai si dans le sous-sous-graphe du coloris col, comme inSG mais aussi avec les 
        même 4 premiers bits de l'opacité."""
        return self.coloris>>4 == col>>4

    def inSSSG(self,col):
        """Retourne vrai si dans le sous-sous-sous-graphe du coloris col, 
        même coloris incluant l'opacité."""
        return self.coloris == col

    def masqueit(self,masque):
        """ Applique le masque et retourne le resultat. Si >0, il y a des bits correspondant. """
        return self.coloris & masque

    def __lt__(self, other):
        return True

    def __repr__(self):
        if self.box is not None:
            return "noeud:{0} pos:{1}".format(self.entity._guid, self.box.pos)
        else:
            return "noeud:{0}".format(self.entity._guid)

class RenderNoeud(ecs.System):
    """Systeme pour le rendering des noeuds via coloriage."""
    def __init__(self, canvas):
        super().__init__()
        self.canvas=canvas

    def init(self):
        pass

    def reset(self):
        pass

    def update(self, dt):
        with self.canvas:
            for entity, noeud in self.entity_manager.pairs_for_type(Noeud):
                Color((noeud.coloris >> 24 & 0xFF)/255.0, (noeud.coloris >> 16 & 0xFF)/255.0, 
                      (noeud.coloris >> 8 & 0xFF)/255.0, (noeud.coloris & 0xFF)/255.0)
                Rectangle(pos=noeud.box.pos, size=noeud.box.size)
                Color(0,0,0,1) # toujours un coutour noir
                Line(rectangle=noeud.box.pos+noeud.box.size)


class Arete(ecs.Component):
    """L'un des deux éléments structurels du graphe' l'autre est le ``Noeud``.
    Le flag ``barriere`` est un indicateur contextuel donnant un hint sur
    l'impact de traverser cette arête. C'est surtout utile pour marquer des
    transition structurelle (ex: entre des cuves et un passage), ou contrôler
    l'accès comme avec une porte ou une barrière (ex: si un seul véhicule
    peut visiter une zone).
    """
    def __init__(self, entity, fr, to):
        """:param entity: on garde un handle vers l'entité père
        :type entity: :class:`ecs.models.Entity`
        :param fr: noeud origine de l'arête
        :type fr: :class:`Noeud`
        :param to: noeud destination de l'arête
        :type to: :class:`Noeud`
        """
        self.entity=entity
        self.fr=fr
        self.to=to
        self.barriere=False


class Phys(ecs.Component):
    """Aspect physique d'un ``Noeud`` du graphe. Variables d'état:

         * dim (couple float): donne les dimensions physique en metres selon (x,y)
         * vol (couple int): est une densite d'occupation spatiale au sol et en hauteur

    A priori, toutes les entités avec un ``Noeud`` et pouvant héberger un mobile doivent 
    avoir un composant ``Phys``. L'échelle de conversion en pixels pour le rendering de la 
    position d'un mobile est déduite de la ``Box``. Il est possible que le scaling change 
    en fonction du noeud, reflétant l'écart entre l'échelle physique et l'échelle de rendering. 
    Bien que ceci puisse être perceptible à l'oeil, ça n'engendre pas d'erreur numérique. 
    Cependant, des distortions trop grandes pourraient perturber l'algorithme de recherche 
    de chemin (A*).
    """
    def __init__(self, n):
        """:param n: on garde un handle vers le composant noeud frère
        :type n: :class:`Noeud`
        """
        self.noeud=n # handle sur le noeud
        self.dim=(6.0,5.0) # dimension (x,y) en metres (couple float)
        self.vol=(80,0) # densite au sol et en hauteur (couple int)        

