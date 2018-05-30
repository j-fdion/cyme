"""
Kanban des opérations.
----------------------
"""

import re



class MetaOperation(type):
    """
    Metaclasse qui permet l'enregistrement de tous les classes qui héritent de la
    classe Operation. À noter qu'il faut les importer avant MetaOperation pour qu'elles
    soient disponibles dans le registre
    """
    registry = {}

    def __new__(cls, clsname, bases, attrs):
        newclass = super(MetaOperation, cls).__new__(cls, clsname, bases, attrs)
        newclass.name = clsname
        MetaOperation.register(newclass)
        return newclass

    @staticmethod
    def register(cls):
        MetaOperation.registry[cls.__name__] = cls
        return cls

    @staticmethod
    def get(clsname):
        try:
            return MetaOperation.registry[clsname]
        except KeyError:
            raise OperationNotImplemented("{" + clsname + "}")


class Operation(metaclass=MetaOperation):
    """
    Classe de base de pour les opérations des ponts.
    Les méthodes precondtion, pretache, tache, postcondition et posttache
    retournent par défaut true pour ne pas empêcher l'exécution du bt si
    elles n'ont pas été implémenté dans les classes qui héritent de cette classe.
    """
    duree = 0
    color = (0,0,0)

    @classmethod
    def get_duree(cls, context=None):
        return cls.duree

    @classmethod
    def get_color(cls):
        return cls.color

    @classmethod
    def precondition(cls, context=None):
        return True

    @classmethod
    def pretache(cls, pont):
        pont.is_operation = True
        return True

    @classmethod
    def tache(cls, kanban):
        kanban.noeud.box.contour_color = (0, 0, 0)
        kanban.noeud.box.color = kanban.operation.get_color()
        kanban.set_next_target()
        return True

    @classmethod
    def postcondition(cls, context=None):
        return True

    @classmethod
    def posttache(cls, pont):
        pont.is_operation = False
        return True


class Kanban(object):
    def __init__(self, token):
        self.operation = MetaOperation.get(token)
        self.croissant = True
        self.debut = 0
        self.cuve_max = 24
        self.cuve_courante = 0
        self.noeud = None
        self.extra = None
        self.pont = None
        self.actif = True #True, le pont peut commencer aussitôt recu
        self.actif_defaut = True
        self.completed = False
        self.temps_termine = 0
        self.temps_restant = 0

    def reset(self):
        self.cuve_courante = 0
        self.temps_termine = 0
        self.pont = None
        self.completed = False
        self.actif = self.actif_defaut

    def init_current_target(self, secteur):
        indice = self.debut + self.cuve_courante
        if indice < len(secteur.noeuds_cuves):
            self.noeud = secteur.noeuds_cuves[indice]
            return self.noeud
        else:
            return None

    def get_current_target(self, secteur):
        indice = self.debut + self.cuve_courante
        if indice < len(secteur.noeuds_cuves):
            self.noeud = secteur.noeuds_cuves[indice]
            return self.noeud
        else:
            return None

    def set_next_target(self):
        if self.cuve_courante < self.cuve_max:
            self.cuve_courante += 1
            if self.cuve_courante >= self.cuve_max:
                self.completed = True

    def is_completed(self):
        return self.completed

    def __str__(self):
        return "{0} {1} {2}".format(self.operation.name, self.debut, self.cuve_max)

    def __repr__(self):
        return "{0} {1} {2}".format(self.operation.name, self.debut, self.cuve_max)

    def to_str(self):
        return "{0} {1} {2}".format(self.operation.name, self.debut, self.cuve_max)


class KanbanParser(object):
    regex_pattern = r"([a-zA-Z]+)([0-9]+)_?([0-9]+)?_?([a-z]+)?"

    @staticmethod
    def string_to_kanbans_list(s):
        kanbans_str = s.replace(" ", "").replace("\t", "").replace("\n", "")
        tokens = kanbans_str.split(",")
        kanbans = []
        for token1 in tokens:
            preprocessed_tokens = KanbanParser.preprocess_token(token1)
            for token2 in preprocessed_tokens:
                kanbans.append(KanbanParser.process_token(token2))
        return kanbans

    @staticmethod
    def preprocess_token(token):
        match = re.match(KanbanParser.regex_pattern, token, re.I)
        if match:
            operation_type = "NONE"
            begin = 0
            count = 0
            extra = ""
            items = match.groups()
            preprocessed_tokens = []
            if items[0]:
                operation_type = items[0]
            if items[1]:
                begin = int(items[1])
            if items[2]:
                count = int(items[2])
            else:
                count = 1
            if items[3]:
                extra = str(items[3]).upper()
            for i in range(count):
                if extra == "":
                    preprocessed_tokens.append("{type}{begin}_{number_to_visit}".format(type=operation_type, begin=begin+i,
                                                                                        number_to_visit=1))
                else:
                    preprocessed_tokens.append("{type}{begin}_{number_to_visit}_{extra}".format(type=operation_type, begin=begin+i,
                                                                                   number_to_visit=1, extra=extra))
            return preprocessed_tokens
        else:
            raise ParsingException("{0} doit être dans le format: ([a-zA-Z]+)([0-9]+)_?([0-9]+)?_?([a-z]+)?".format(token))

    @staticmethod
    def process_token(token):
        kanban = None
        match = re.match(KanbanParser.regex_pattern, token, re.I)
        op = ' '
        if match:
            items = match.groups()
            if items[0]:
                kanban = Kanban(items[0])
                kanban.croissant = op.isupper()
            if items[1]:
                kanban.debut = int(items[1]) - 1
            if items[2]:
                kanban.cuve_max = int(items[2])
            else:
                kanban.cuve_max = 1
            if items[3]:
                kanban.extra = str(items[3]).upper()
        else:
            raise ParsingException("{0} doit être dans le format: ([a-zA-Z]+)([0-9]+)_?([0-9]+)?_?([a-z]+)?".format(token))

        return kanban


class DelayedKanban(object):
    def __init__(self, token):
        self.operation = MetaOperation.get(token)
        self.duree = 0
        self.t_trigger = 0
        self.pont = None
        self.completed = False
        self.temps_termine = 0
        self.extra = None
        self.temps_restant = 0

    def reset(self):
        self.temps_termine = 0
        self.pont = None
        self.completed = False

    def is_completed(self):
        return self.completed

    def __str__(self):
        return "{0} {1} {2}".format(self.operation.name, self.duree, self.t_trigger)

    def __repr__(self):
        return "{0} {1} {2}".format(self.operation.name, self.duree, self.t_trigger)

    def to_str(self):
        return "{0} {1} {2}".format(self.operation.name, self.duree, self.t_trigger)


class DelayedKanbanParser(object):
    regex_pattern = r"([a-zA-Z]+)([0-9]+)_?([0-9]+)?_?([a-z]+)?"

    @staticmethod
    def string_to_list(s):
        pauses_str = s.replace(" ", "").replace("\t", "").replace("\n", "")
        tokens = pauses_str.split(",")
        pauses = []
        for token1 in tokens:
            pauses.append(DelayedKanbanParser.process_token(token1))
        return pauses

    @staticmethod
    def process_token(token):
        pause = None
        match = re.match(DelayedKanbanParser.regex_pattern, token, re.I)
        if match:
            items = match.groups()
            if items[0]:
                pause = DelayedKanban(items[0])
            if items[1]:
                pause.duree = int(items[1])
            if items[2]:
                pause.t_trigger = int(items[2])
            else:
                pause.t_trigger = 0
            if items[3]:
                pause.extra = str(items[3]).upper()
        else:
            raise ParsingException("{0} doit être dans le format: ([a-zA-Z]+)([0-9]+)_?([0-9]+)?_?([a-z]+)?".format(token))
        return pause


class DeltaKanban(object):
    def __init__(self, token):
        self.operation = MetaOperation.get(token)
        self.debut = 0
        self.cuve_max = 1
        self.cuve_courante = 0
        self.delta = 0
        self.pont = None
        self.completed = False
        self.temps_termine = 0
        self.noeud = None
        self.extra = None
        self.temps_restant = 0

    def is_completed(self):
        return self.completed

    def reset(self):
        self.cuve_courante = 0
        self.temps_termine = 0
        self.pont = None
        self.completed = False

    def init_current_target(self, secteur):
        indice = self.debut + self.cuve_courante
        if indice < len(secteur.noeuds_cuves):
            self.noeud = secteur.noeuds_cuves[indice]
            return self.noeud
        else:
            return None

    def get_current_target(self, secteur):
        indice = self.debut + self.cuve_courante
        if indice < len(secteur.noeuds_cuves):
            self.noeud = secteur.noeuds_cuves[indice]
            return self.noeud
        else:
            return None

    def set_next_target(self):
        if self.cuve_courante < self.cuve_max:
            self.cuve_courante += 1
            if self.cuve_courante >= self.cuve_max:
                self.completed = True

    def __str__(self):
        return "{0} {1} {2}".format(self.operation.name, self.debut, self.delta)

    def __repr__(self):
        return "{0} {1} {2}".format(self.operation.name, self.debut, self.delta)

    def to_str(self):
        return "{0} {1} {2}".format(self.operation.name, self.debut, self.delta)


class DeltaKanbanParser(object):
    regex_pattern = r"([a-zA-Z]+)([0-9]+)_?([0-9]+)?_?([a-z]+)?"

    @staticmethod
    def string_to_list(s):
        dk_str = s.replace(" ", "").replace("\t", "").replace("\n", "")
        tokens = dk_str.split(",")
        dk = []
        for token1 in tokens:
            dk.append(DeltaKanbanParser.process_token(token1))
        return dk

    @staticmethod
    def process_token(token):
        dk = None
        match = re.match(DeltaKanbanParser.regex_pattern, token, re.I)
        if match:
            items = match.groups()
            if items[0]:
                dk = DeltaKanban(items[0])
            if items[1]:
                dk.debut = int(items[1]) - 1
            if items[2]:
                dk.delta = int(items[2])
            else:
                dk.delta = 0
            if items[3]:
                dk.extra = str(items[3]).upper()
        else:
            raise ParsingException("{0} doit être dans le format: ([a-zA-Z]+)([0-9]+)_?([0-9]+)?_?([a-z]+)?".format(token))
        return dk


class ParsingException(Exception):
    pass


class OperationNotImplemented(Exception):
    pass
