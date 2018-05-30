from .. import bt

class ScanObjectifs(bt.Task):

    def __init__(self, vehicule):
        super().__init__()
        self.vehicule = vehicule

    def trouve_objectif_aller(self):
        print("cibles_aller", len(self.vehicule.cibles_aller))
        while True:
            try:
                noeud = self.vehicule.cibles_aller.pop()
            except IndexError:
                return None
            else:
                if noeud.allee.need_cab_ea or noeud.allee.need_ben_vide:
                    print(len(self.vehicule.cibles_aller))
                    return noeud


    def trouve_objectif_retour(self):
        print("cibles_retour", len(self.vehicule.cibles_retour))
        while True:
            try:
                noeud = self.vehicule.cibles_retour.pop()
            except IndexError:
                return None
            else:
                if noeud.allee.has_cab_megot or noeud.allee.has_ben_pleine:
                    print(len(self.vehicule.cibles_retour))
                    return noeud

    def run(self):
        if self.vehicule.objectif_aller is None and self.vehicule.objectif_retour is None:
            self.vehicule.objectif_aller = self.trouve_objectif_aller()
            self.vehicule.objectif_retour = self.trouve_objectif_retour()

        if self.vehicule.objectif_aller is not None or self.vehicule.objectif_retour is not None:
            #print("ScanObjectifs", bt.Task.SUCCES)
            return bt.Task.SUCCES
        else:
            print("ScanObjectifs", bt.Task.ECHEC, self.vehicule.objectif_aller, self.vehicule.objectif_retour)
            return bt.Task.ECHEC

class ObjectifAllerExiste(bt.Task):

    def __init__(self, vehicule):
        super().__init__()
        self.vehicule = vehicule

    def run(self):
        value = bt.Task.SUCCES if self.vehicule.objectif_aller is not None else bt.Task.ECHEC
        self.vehicule.objectif_aller.box.color = (1,0,0)
        print("ObjectifAllerExiste", self.vehicule.objectif_aller, value == bt.Task.SUCCES)
        return value

class ObjectifRetourExiste(bt.Task):

    def __init__(self, vehicule):
        super().__init__()
        self.vehicule = vehicule

    def run(self):
        value = bt.Task.SUCCES if self.vehicule.objectif_retour is not None else bt.Task.ECHEC
        print("ObjectifRetourExiste", value == bt.Task.SUCCES)
        return value

class ContientCabBen(bt.Task):

    def __init__(self, vehicule):
        super().__init__()
        self.vehicule = vehicule

    def run(self):
        value = bt.Task.SUCCES if self.vehicule.cab or self.vehicule.ben else bt.Task.ECHEC
        print("ContientCabBen", self.vehicule.cab, self.vehicule.ben, value == bt.Task.SUCCES)
        return value

class MoveToLocation(bt.Task):
    """ Demande au composant mobile de se déplacer vers location
    """
    def __init__(self, vehicule, location):
        super().__init__()
        self.vehicule = vehicule
        self.location = location

    def run(self):
        """
        :return: ``bt.Task.SUCCES`` si le vehicule est positionné au dessus de sa cible
        """
        if self.vehicule.mobile.target != self.location:
            self.vehicule.mobile.target = self.location

        value = bt.Task.SUCCES if self.vehicule.mobile.target == self.vehicule.mobile.npos else bt.Task.ECHEC
        print("MoveToLocation", self.location, value == bt.Task.SUCCES)
        return value

class MoveToObjectifAller(bt.Task):
    """ Demande au composant mobile de se déplacer vers l'objectif courant
    """

    def __init__(self, vehicule):
        super().__init__()
        self.vehicule = vehicule

    def run(self):
        """
        :return: ``bt.Task.SUCCES`` si le vehicule est positionné au dessus de sa cible
        """
        if self.vehicule.mobile.target != self.vehicule.objectif_aller:
            self.vehicule.mobile.target = self.vehicule.objectif_aller

        value = bt.Task.SUCCES if self.vehicule.mobile.target == self.vehicule.mobile.npos else bt.Task.RUNNING
        print("MoveToObjectifAller", self.vehicule.objectif_aller, value == bt.Task.SUCCES)
        return value

class MoveToObjectifRetour(bt.Task):
    """ Demande au composant mobile de se déplacer vers l'objectif courant
    """

    def __init__(self, vehicule):
        super().__init__()
        self.vehicule = vehicule

    def run(self):
        """
        :return: ``bt.Task.SUCCES`` si le vehicule est positionné au dessus de sa cible
        """
        if self.vehicule.mobile.target != self.vehicule.objectif_retour:
            self.vehicule.mobile.target = self.vehicule.objectif_retour

        value = bt.Task.SUCCES if self.vehicule.mobile.target == self.vehicule.mobile.npos else bt.Task.RUNNING
        print("MoveToObjectifRetour", self.vehicule.objectif_aller, value == bt.Task.SUCCES)
        return value

class IsBenVide(bt.Task):

    def __init__(self, vehicule):
        super().__init__()
        self.vehicule = vehicule

    def run(self):
        value = bt.Task.SUCCES if self.vehicule.objectif_aller.allee.need_ben_vide else bt.Task.ECHEC
        print("IsBenVide", value == bt.Task.SUCCES)
        return value

class IsBenPleine(bt.Task):

    def __init__(self, vehicule):
        super().__init__()
        self.vehicule = vehicule

    def run(self):
        value = bt.Task.SUCCES if self.vehicule.objectif_retour.allee.has_ben_plein else bt.Task.ECHEC
        print("IsBenPleine", value == bt.Task.SUCCES)
        return value

class DeposerBenPleine(bt.Task):

    def __init__(self, vehicule):
        super().__init__()
        self.vehicule = vehicule

    def run(self):
        print("DeposerBenPleine")
        self.vehicule.ben = False
        self.vehicule.objectif_retour = None
        return bt.Task.SUCCES

class RamasserBenPleine(bt.Task):

    def __init__(self, vehicule):
        super().__init__()
        self.vehicule = vehicule

    def run(self):
        print("RamasserBenPleine")
        self.vehicule.objectif_retour.allee.has_ben_pleine = False
        self.vehicule.objectif_retour.allee.ben = -1
        self.vehicule.ben = True
        return bt.Task.SUCCES

class DeposerBenVide(bt.Task):

    def __init__(self, vehicule):
        super().__init__()
        self.vehicule = vehicule

    def run(self):
        print("DeposerBenVide")
        self.vehicule.objectif_aller.allee.need_ben_vide = False
        self.vehicule.objectif_aller.allee.ben = 0
        self.vehicule.objectif_aller = None
        self.vehicule.ben = False
        return bt.Task.SUCCES

class RamasserBenVide(bt.Task):

    def __init__(self, vehicule):
        super().__init__()
        self.vehicule = vehicule

    def run(self):
        print("RamasserBenVide")
        self.vehicule.ben = True
        return bt.Task.SUCCES

class DeposerCabEa(bt.Task):
    def __init__(self, vehicule):
        super().__init__()
        self.vehicule = vehicule

    def run(self):
        print("DeposerCabEa")
        self.vehicule.objectif_aller.allee.need_cab_ea = False
        self.vehicule.objectif_aller.allee.cab = 3
        self.vehicule.objectif_aller = None
        self.vehicule.cab = False
        return bt.Task.SUCCES


class RamasserCabEa(bt.Task):
    def __init__(self, vehicule):
        super().__init__()
        self.vehicule = vehicule

    def run(self):
        print("RamasserCabEa")
        self.vehicule.cab = True
        return bt.Task.SUCCES


class DeposerCabMegot(bt.Task):
    def __init__(self, vehicule):
        super().__init__()
        self.vehicule = vehicule

    def run(self):
        print("DeposerCabMegot")
        self.vehicule.cab = False
        self.vehicule.objectif_retour = None
        return bt.Task.SUCCES


class RamasserCabMegot(bt.Task):
    def __init__(self, vehicule):
        super().__init__()
        self.vehicule = vehicule

    def run(self):
        print("RamasserCabMegot")
        self.vehicule.objectif_retour.allee.has_cab_megot = False
        self.vehicule.objectif_retour.allee.megot = 0
        self.vehicule.cab = True

        return bt.Task.SUCCES


class IsCabEa(bt.Task):

    def __init__(self, vehicule):
        super().__init__()
        self.vehicule = vehicule

    def run(self):
        value = bt.Task.SUCCES if self.vehicule.objectif_aller.allee.need_cab_ea else bt.Task.ECHEC
        print("IsCabEa", value == bt.Task.SUCCES)
        return value

class IsCabMegot(bt.Task):
    def __init__(self, vehicule):
        super().__init__()
        self.vehicule = vehicule

    def run(self):
        value = bt.Task.SUCCES if self.vehicule.objectif_retour.allee.has_cab_megot else bt.Task.ECHEC
        print("IsCabMegot", value == bt.Task.SUCCES)
        return value