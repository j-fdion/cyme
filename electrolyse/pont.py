"""
Composants et systèmes reliés aux ponts.
----------------------------------------

Le concept de :class:`Pont` est un composant associé à un :class:`cyme.simulation.graphe.Noeud`, capable de se déplacer sur un graphe représentant des cuves. Le behavior tree ci-dessous montre l'IA de la machine. Essentiellement, on boucle sur les étapes:

  * si le pont est utilisable (c'est-à-dire dans un état où il n'est pas brisé)
  * si l'opérateur n'est pas en pause
  * si le pont doit participer à un "move prioritaire", par exemple un transbordement qui nécessite le déplacement de plusiers ponts.
  * si le pont est positionné par dessus la bonne cuve (Kanban.get_current_target())
  * laisser passer un temps de réalisation (Delay) pour la tâche en cours (Kanban)

Avec le système gestionnaire_pont, les ponts permettent de représenter la majorité des opérations qui sont exécutées dans un centre d'électrolyse.

.. image::  images/bt_pont.png
    :align: center

Afin de garder le behavior tree le plus réactif possible l'exéction d'un Kanban est fait d'une manière non-atomique.
Le Kanban en cours peut être mis en pause ou annulé par le système gestionnaire_pont si on le pont est nécessaire à une tâche plus importante, par exemple un transbordement.
Le pont devra exécuter le même Kanban tant que le booléen "completed" n'est pas vrai.


"""

from collections import deque

from kivy.core.text import Label as CoreLabel
from kivy.graphics.context_instructions import Color, PushMatrix, PopMatrix, Rotate, Translate
from kivy.graphics.vertex_instructions import Rectangle, Line

from .. import ecs
from .. import bt

from . import bt_pont
from .. import simulation


class Pont(ecs.Component):
    MSE, PACD, MTC = range(3)

    def __init__(self, nom, index, mobile=None, entity_manager=None, noeud_entrepot=None):
        self.nom = nom
        self.root = None
        self.mobile = mobile
        self.nature = Pont.MSE
        self.secteur = None

        self.kanbans = deque([])
        self.kanbans_lock = False
        self.is_operation = False
        self.bris = deque([])
        self.is_bris = False
        self.pauses = deque([])
        self.is_pause = False
        self.rdc = deque([])
        self.is_rdc = False

        self.entity_manager = entity_manager
        self.noeud_entrepot = noeud_entrepot
        self.gestionnaire_pont = None

        self.setup_behavior()

    def set_gestionnaire_pont(self, gestionnaire):
        self.gestionnaire_pont = gestionnaire

    def setup_behavior(self):
        """ Setup du behavior tree pour le traitements des files de kanbans
            C'est ici qu'on fait les ajustements nécessaires pour les arbres bris, pauses et kanbans
            Notamment on ajoute le noeud déplacement du mobile en pretache pour le bt kanbans
        """
        self.root = bt.Selector()

        parallel_bris_pauses = bt.Parallel()
        self.root.add_child(parallel_bris_pauses)

        bris = self.setup_behavior_kanban("bris")
        pauses = self.setup_behavior_kanban("pauses")
        parallel_bris_pauses.add_child(bris)
        parallel_bris_pauses.add_child(pauses)

        parallel_kanbans_rdc = bt.Parallel()
        self.root.add_child(parallel_kanbans_rdc)

        inverter = bt.Inverter()
        inverter.add_child(bt_pont.IsLocked(self))

        kanbans = self.setup_behavior_kanban("kanbans", preconditions=[inverter], pretaches=[bt_pont.MoveToTarget(self, "kanbans")])
        parallel_kanbans_rdc.add_child(kanbans)

        rdc = self.setup_behavior_kanban("rdc", pretaches=[bt_pont.MoveToTarget(self, "rdc")])
        parallel_kanbans_rdc.add_child(rdc)


    def setup_behavior_kanban(self, queue, preconditions=list(), pretaches=list(), postconditions=list(), posttaches=list()):
        """ Setup du behavior tree de base pour le traitement des files de kanban
            L'argument queue est le nom de la file qui doit être affectée par le bt, soit kanbans, pauses ou bris.
            Les arguments preconditions, pretaches, postconditions et posttaches permettent de
            d'ajouter des comportements supplémentaires aux principaux composants  de l'arbre.
         """
        root = bt.SequenceStar()
        inverter = bt.Inverter()
        inverter.add_child(bt_pont.IsQueueEmpty(self, queue))
        root.add_child(inverter)

        root.add_child(bt_pont.Precondition(self, queue))
        for precondition in preconditions:
            root.add_child(precondition)

        root.add_child(bt_pont.Pretache(self, queue))
        for pretache in pretaches:
            root.add_child(pretache)

        root.add_child(bt_pont.Tache(self, queue))

        root.add_child(bt_pont.Postcondition(self, queue))
        for postcondition in postconditions:
            root.add_child(postcondition)

        root.add_child(bt_pont.Posttache(self, queue))
        for posttache in posttaches:
            root.add_child(posttache)
        return root

    def __repr__(self):
        return "{0}".format(self.nom)

    def update(self):
        """Update du bb et du bt."""
        self.root.run()


class RenderPont(ecs.System):
    """Systeme pour le rendering des ponts."""



    def __init__(self, canvas, couleurs, textures):
        super().__init__()
        self.canvas = canvas
        self.couleurs = couleurs
        self.textures = textures
        self.cadran = None

    def init(self):
        pass

    def reset(self):
        pass

    def set_cadran(self):
        # Pour reference seulement
        # On split l'écran en 4 cadrans
        # index, position, size
        # BG = (0, (0,0),(550,350))
        # BD = (1, (550,0),(550,350))
        # HG = (2, (0,350),(550,350))
        # HD = (3, (550,350),(550,350))
        self.cadran = [[], [], [], []]
        for entity, pont in self.entity_manager.pairs_for_type(Pont):
            x = pont.mobile.noeud.box.pos[0]
            y = pont.mobile.noeud.box.pos[1]
            if y < 350:
                if x < 550:
                    self.cadran[0].append(pont)
                    pont.cadran = 0
                    pont.position_label = 0
                else:
                    self.cadran[1].append(pont)
                    pont.cadran = 1
                    pont.position_label = 0
            else:
                if x < 550:
                    self.cadran[2].append(pont)
                    pont.cadran = 2
                    pont.position_label = 0
                else:
                    self.cadran[3].append(pont)
                    pont.cadran = 3
                    pont.position_label = 0

    def set_postion_label(self):
        for cadran in self.cadran:
            if len(cadran) > 1:
                for i, pont in enumerate(cadran):
                    if i == 0:
                        continue
                    pont.position_label += i * 30

    def draw_text(self, text, font_size, x, y):
        label = CoreLabel(text="{0}".format(text), font_size=font_size)
        label.refresh()
        texture = label.texture
        Rectangle(size=texture.size, pos=(x,y), texture=texture)

    def draw_text_with_rotation(self, text, font_size, x, y, angle):
        PushMatrix()
        label = CoreLabel(text="{0}".format(text), font_size=font_size)
        label.refresh()
        texture = label.texture
        Translate(x, y)
        Rotate(angle, 0, 0, 1)
        Rectangle(size=texture.size, pos=(0, 0), texture=texture)
        PopMatrix()

    def temps_total_completion(self, pont):
        t = 0
        for k in pont.kanbans:
            t += k.operation.get_duree(pont)
        return t

    def update(self, dt):
        #self.set_cadran()
        #self.set_postion_label()
        with self.canvas.after:
            label_pont_x, label_pont_y = (40,25)
            for entity, pont in self.entity_manager.pairs_for_type(Pont):
                box = pont.mobile.noeud.box
                Color(box.color[0], box.color[1], box.color[2], box.alpha)
                Rectangle(pos=box.pos, size=box.size)
                Color(box.contour_color[0], box.contour_color[1], box.contour_color[2], box.alpha)
                Line(rectangle=box.pos + (12, 36))
                self.draw_text(pont.nom, 14, box.pos[0], box.pos[1] + 40)

            for entity, pont in self.entity_manager.pairs_for_type(Pont):
                PopMatrix()
                self.draw_text(pont.nom, 14, label_pont_x - 30, label_pont_y)
                queue_names = ["kanbans", "pauses", "bris", "rdc"]
                x, y = label_pont_x, label_pont_y
                for queue_name in queue_names:
                    x = label_pont_x
                    queue = getattr(pont, queue_name)
                    old_name = ""
                    if queue:
                        Color(0,0,0,1)
                        t = queue[0].temps_restant
                        seconde = t % 3600
                        minute = seconde // 60
                        seconde = seconde % 60
                        self.draw_text("[{0:02d}m{1:02d}s]".format(minute, seconde), 12, x-10, y)
                        if queue_name == "kanbans":
                            t = self.temps_total_completion(pont)
                            heure = t // 3600
                            seconde = t % 3600
                            minute = seconde // 60
                            seconde = seconde % 60
                            self.draw_text("[{0:02d}h{1:02d}m{2:02d}s]".format(heure, minute, seconde), 12, x - 10, y-20)
                        for i, kanban in enumerate(queue):
                            kanban_position_x = 50
                            if i < 79:
                                color = kanban.operation.get_color()
                                Color(color[0], color[1], color[2], 1)
                                Rectangle(pos=(x+kanban_position_x,y), size=(16,16))
                                if isinstance(kanban, simulation.kanban.Kanban):
                                    Color(0,0,0,1)
                                    self.draw_text("{0:02d}".format(kanban.debut+1), 11, x+kanban_position_x+2, y)
                                elif isinstance(kanban, simulation.kanban.DelayedKanban):
                                    Color(0,0,0,1)
                                    self.draw_text("{0:02d}".format(kanban.duree//60), 11, x+kanban_position_x+2, y)
                                elif isinstance(kanban, simulation.kanban.DeltaKanban):
                                    Color(0,0,0,1)
                                    self.draw_text("{0:02d}".format(kanban.debut+1), 11, x+kanban_position_x+2, y)
                                if kanban.operation.name != old_name:
                                    Color(0,0,0,1)
                                    self.draw_text_with_rotation(kanban.operation.name, 12, x+kanban_position_x, y+5, 45)
                                    old_name = kanban.operation.name
                            else:
                                Color(0, 0, 0, 1)
                                self.draw_text("...",14,x+kanban_position_x, y)
                                break
                            x += 20
                        y += 30
                label_pont_y += 100
                PushMatrix()
