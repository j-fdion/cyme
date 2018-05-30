from collections import defaultdict, namedtuple
import statistics
from itertools import chain

from kivy.graphics.context_instructions import Color
from kivy.graphics.vertex_instructions import Rectangle, Line
from kivy.core.text import Label as CoreLabel

from .. import ecs
from .pont import Pont
from .centre import Secteur
from .. import simulation


class StatistiquePoste(ecs.System):
    def __init__(self):
        super().__init__()
        self.ponts = []
        self.secteurs = []

        nested_dict = lambda: defaultdict(nested_dict)
        self.toc = nested_dict()
        self.pause = nested_dict()
        self.ret = nested_dict()
        self.gest = nested_dict()

        self.cuve_non_siph = []
        self.anode_non_change = []

        self.moy_toc = nested_dict()
        self.moy_pause = nested_dict()
        self.moy_ret = nested_dict()
        self.moy_gest = nested_dict()

        self.max_toc = nested_dict()
        self.max_ret = nested_dict()
        self.non_termine = nested_dict()
        self.non_termine_temp = nested_dict()

    def init(self):
        for entity, secteur in self.entity_manager.pairs_for_type(Secteur):
            self.secteurs.append(secteur)

        for entity, pont in self.entity_manager.pairs_for_type(Pont):
            self.ponts.append(pont)

        for secteur in self.secteurs:
            for poste in range(secteur.num_quart_max()):
                self.toc[secteur] = 0
                self.pause[secteur] = 0
                self.ret[secteur] = 0

                self.moy_toc[secteur][poste] = []
                self.moy_pause[secteur][poste] = []
                self.moy_ret[secteur][poste] = []

                self.max_toc[secteur][poste] = []
                self.max_ret[secteur][poste] = []
                self.non_termine[secteur][poste] = []
                self.non_termine_temp[secteur] = 0

    def reset(self):
        for secteur in self.secteurs:
            for poste in range(secteur.num_quart_max()):
                self.toc[secteur] = 0
                self.pause[secteur] = 0
                self.ret[secteur] = 0
                self.non_termine_temp[secteur] = 0

    def update(self, dt):
        for pont in self.ponts:
            if pont.secteur is not None:
                if pont.is_bris:
                    self.ret[pont.secteur] += 1
                else:
                    if pont.is_pause:
                        self.pause[pont.secteur] += 1
                    else:
                        if pont.is_operation:
                            self.toc[pont.secteur] += 1

    def calculate_temps_kanban(self, kanban):
        cuve_restante = kanban.cuve_max - kanban.cuve_courante
        temps = cuve_restante * kanban.operation.get_duree()
        return temps

    def get_temps_necessaire_for_completion(self, secteur):
        temps = 0
        kanbans = secteur.get_kanbans_for_current_quart()
        for kanban in kanbans:
            if not kanban.is_completed():
                cuve_restante = kanban.cuve_max - kanban.cuve_courante
                t = cuve_restante * kanban.operation.get_duree(secteur.pont)
                kanban.temps_necessaire = t
                temps += t
        return temps

    def compile_statistics(self):
        self.temps_necessaire = 0
        non_termine = []
        for secteur in self.secteurs:
            self.temps_necessaire = self.get_temps_necessaire_for_completion(secteur)
            for kanban in secteur.get_kanbans_for_current_quart():
                if not kanban.is_completed():
                    non_termine.append(kanban)

        for secteur in self.secteurs:
            poste = secteur.num_quart
            self.moy_toc[secteur][poste].append(self.toc[secteur])
            self.moy_ret[secteur][poste].append(self.ret[secteur])
            self.moy_pause[secteur][poste].append(self.pause[secteur])

        for secteur in self.secteurs:
            poste = secteur.num_quart
            print("num quart:", poste)

            moy = statistics.mean(self.moy_toc[secteur][poste])
            print("tache:\t", end='')
            print("{0}%".format(int(moy / 43200 * 100)), simulation.base.Moment.seconds_to_hhmmss(int(moy)))

            moy2 = statistics.mean(self.moy_ret[secteur][poste])
            print("bris:\t", end='')
            print("{0}%".format(int(moy2 / 43200 * 100)), simulation.base.Moment.seconds_to_hhmmss(int(moy2)))

            moy3 = statistics.mean(self.moy_pause[secteur][poste])
            print("pause:\t", end='')
            print("{0}%".format(int(moy3 / 43200 * 100)), simulation.base.Moment.seconds_to_hhmmss(int(moy3)))

            print("total:\t", end='')
            print("{0}%".format(int((moy + moy2 + moy3) / 43200 * 100)),
                  simulation.base.Moment.seconds_to_hhmmss(int(moy + moy2 + moy3)))

            print("----")

        for kb in non_termine:
            for secteur in self.secteurs:
                kanbans = secteur.get_kanbans_for_current_quart()
                if kb in kanbans:
                    self.non_termine_temp[secteur] += kb.temps_necessaire
                    print(secteur.nom, kb.operation.name, "[{0}/{1}]".format(kb.cuve_courante, kb.cuve_max),
                          simulation.base.Moment.seconds_to_hhmmss(kb.temps_necessaire))

        for secteur in self.secteurs:
            poste = secteur.num_quart
            self.non_termine[secteur][poste].append(self.non_termine_temp[secteur] // 60)

        print("Temps total nécessaire pour terminer les tâches restantes:",
              simulation.base.Moment.seconds_to_hhmmss(self.temps_necessaire))

        print(self.non_termine)

        return self.moy_toc, self.moy_ret, self.moy_pause, self.non_termine
