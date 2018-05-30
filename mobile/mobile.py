"""
Composants reliés aux noeuds mobiles.
-------------------------------------
"""

from kivy.graphics.context_instructions import Color, PushMatrix, Rotate, PopMatrix, Translate
from kivy.graphics.vertex_instructions import Rectangle, Line

from .. import bt
from .. import ecs
from .. import simulation
from . import bt_mobile

class Mobile(ecs.Component):
    """Gère tous les déplacements de l'entité via un BT. Variables d'état:

         * vit (float): vitesse de deplacement en m/sec (positif pour un mobile auto-tracté seulement)
         * prel (couple float): position relative de l'entite dans le noeud hôte

    Nécessite d'avoir un composant ``Noeud`` et un ``Phys`` dans l'entité.
    Bien qu'un ``Mobile`` soit une entité avec un ``Noeud``, on exige qu'il soit
    toujours positionné *sur* un autre ``Noeud`` du graphe ayant lui aussi un composant ``Phys``.
    C'est-à-dire que les ``Mobile`` se déplacent sur les ``Noeud`` du graphe, inclunt sur un autre
    ``Mobile``. Par exemple lorsque qu'un pont transbordeur transporte un autre pont.
    On implémente plusieurs variantes de ``move``, dont le saut du centre d'un noeud à un autre,
    sans égard aux collisons. Le temps avant que le saut soit effectif dépend de la distance (d)
    et de la vitesse du mobile (vit): durée = int(d/vit). Afin d'avoir un mouvement plus précis,
    une variante tiens compte de l'évolution de la position du mobile dans les noeuds via ``prel``.
    La position relative (0.5,0.5) est le centre, alors que (0.0,0.0) est le coin inférieur gauche
    et (1.0,1.0) le coin supérieur droit."""

    TIMED_JUMP, JUMP, MOVE = range(3)

    def __init__(self, n, p, npos, nom, type=3, vit=5.0, accl=3.0):
        """:param n: on garde un handle vers le composant noeud frère
        :type n: :class:`Noeud`
        :param p: on garde un handle vers le composant physique frère
        :type p: :class:`Phys`
        :param npos: on garde un handle vers le noeud où est positionné le mobile
        :type npos: :class:`Noeud`
        :param str nom: nom du mobile
        """
        self.noeud=n # handle sur le noeud
        self.phys=p # handle sur la physique
        self.npos=npos # handle sur le noeud du graphe ou se trouve le mobile
        self.ndest=None
        self.target=None
        self.path=[]
        self.isBarriere=False
        self.isMoving=False
        self.nom=nom # nom du mobile
        self.vit=vit # vitesse en m/sec dans la direction de deplacement (ex: 1.0 pour un pont), si type JUMP ou MOVE. Temps en sec pour se déplacer d'un noeud si type TIMED_JUMP
        self.accl=accl
        self.prel=(0.5,0.5) # position relative dans le noeud hote (couple float), defaut est le centre (0.5,0.5)
        self.bb=simulation.base.Blackboard() # un blackboard (memoire)
        self.root = None

        self.masque = 0xffffffff

        self.setup_behavior(type) # on construit l'IA

    def setup_behavior(self, type):
        """Construction du BT définissant le comportement (IA)."""
        self.root = bt.SequenceStar()
        movement = None
        if type == Mobile.JUMP:
            movement = bt_mobile.jumpToDest(self)
        elif type == Mobile.MOVE:
            movement = bt_mobile.moveToDest(self)
        elif type == Mobile.TIMED_JUMP:
            movement = bt_mobile.timedJumpToDest(self)
        #self.root.add_child(bt_mobile.isNDestBloque(self))
        self.root.add_child(movement)

    def update(self):
        """Update du bt."""
        self.root.run()


class RenderChemin(ecs.System):
    def __init__(self, canvas):
        super().__init__()
        self.canvas=canvas

    def init(self):
        pass

    def reset(self):
        pass

    def update(self, dt):
        with self.canvas:
            for entity, mobile in self.entity_manager.pairs_for_type(Mobile):
                for n in mobile.path:
                    Color(0,0,0,1)
                    Rectangle(pos=n.box.pos, size=(10,10))
                if mobile.ndest:
                    Color(1,0,0,1)
                    Rectangle(pos=mobile.ndest.box.pos, size=(10,10))


