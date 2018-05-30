
from collections import defaultdict, deque

from .. import ecs
from . import centre
from . import vehicule

class GestionnaireEa(ecs.System):
    def __init__(self, bd):
        super().__init__()
        self.bd = bd
        self.secteurs = []
        self.vehicules = []
        self.ordres = {}

    def create_famille(self, groupe_nom):
        groupe_secteur = []

        for g in groupe_nom:
            s1 = None
            s2 = None
            s3 = None
            s4 = None
            for entity, secteur in self.entity_manager.pairs_for_type(centre.Secteur):
                if secteur.nom == g[0]:
                    s1 = secteur
                if secteur.nom == g[1]:
                    s2 = secteur
                if secteur.nom == g[2]:
                    s3 = secteur
                if secteur.nom == g[3]:
                    s4 = secteur
            groupe_secteur.append((s1, s2, s3, s4))

        return groupe_secteur

    def create_objectifs_famille(self, groupe_secteur, ordres):
        objectifs_famille = defaultdict(list)
        for i, g in enumerate(groupe_secteur):
            for ordre in ordres:
                objectifs = []
                for o in ordre:
                    index = o[0]
                    debut = o[1]
                    fin = o[2]
                    if debut < fin:
                        n = g[index].noeuds_allees[debut:fin + 1]
                        objectifs.extend(n)
                    else:
                        n = g[index].noeuds_allees[fin:debut][::-1]
                        objectifs.extend(n)
                objectifs_famille[i].append(deque(reversed(objectifs)))
                print(len(objectifs_famille[i]))
        return objectifs_famille

    def init(self):
        groupe_nom = [('T1', 'T2', 'T7', 'T8'), ('G1', 'G2', 'G7', 'G8'), ('B3', 'B4', 'B5', 'B6')]
        groupe_secteur = self.create_famille(groupe_nom)

        ordres = [[(2, 21, 35), (0, 19, 0), (0, 19, 35), (1, 0, 20)],
                 [(1, 21, 35), (3, 19, 0), (3, 19, 35), (2, 0, 20)]]
        objectifs_famille = self.create_objectifs_famille(groupe_secteur, ordres)

        for entity, v in self.entity_manager.pairs_for_type(vehicule.VehiculeEa):
            v.gestionnaire = self
            self.vehicules.append(v)

        for i, v in enumerate(self.vehicules):
            v.cibles_aller = objectifs_famille[i][0]
            v.cibles_retour = objectifs_famille[i][1]
            print(objectifs_famille[i][0])
            for objectif in list(v.cibles_aller):
                objectif.box.color = (1,1,0)
            for objectif in list(v.cibles_retour):
               objectif.box.color = (0,1,1)

    def reset(self):
        pass

    def update(self, dt):
        pass
