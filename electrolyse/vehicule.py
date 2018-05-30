
from collections import deque

from kivy.graphics.context_instructions import Color
from kivy.graphics.vertex_instructions import Rectangle, Line

from .. import ecs
from .. import bt
from . import bt_vehicule

class VehiculeEa(ecs.Component):

    def __init__(self, nom, index, noeud_entrepot, mobile=None, entity_manager=None):
        self.mobile = mobile
        self.entity_manager=entity_manager
        self.noeud_entrepot = noeud_entrepot

        self.cibles_aller = deque()
        self.objectif_aller = None

        self.cibles_retour = deque()
        self.objectif_retour = None

        self.cab = False
        self.ben = False

        self.setup_behavior()

    def update(self):
        self.mobile.root.run()
        self.root.run()

    def setup_behavior(self):
        #niveau 0
        self.root = bt.Sequence()

        scan_objectifs = bt_vehicule.ScanObjectifs(self)
        selector_tache = bt.Selector()
        self.root.add_child(scan_objectifs)
        self.root.add_child(selector_tache)

        #--------------------------------------------------
        #objectif aller
        #--------------------------------------------------

        seq_aller = bt.Sequence()
        obj_aller_existe = bt_vehicule.ObjectifAllerExiste(self)
        repeat_until_success_aller = bt.RepeatUntilSucces()

        seq_aller.add_child(obj_aller_existe)
        seq_aller.add_child(repeat_until_success_aller)

        seq_aller_ramasser_deposer = bt.SequenceStar()
        seq_aller_ramasser = bt.SequenceStar()
        seq_aller_deposer = bt.SequenceStar()

        repeat_until_success_aller.add_child(seq_aller_ramasser_deposer)
        seq_aller_ramasser_deposer.add_child(seq_aller_ramasser)
        seq_aller_ramasser_deposer.add_child(seq_aller_deposer)

        ##--------------------------------------------------
        ##ramasser entrepot cab ea ou ben vide
        ##--------------------------------------------------

        contient_cab_ben1 = bt_vehicule.ContientCabBen(self)
        contient_cab_ben2 = bt_vehicule.ContientCabBen(self)
        inverter_contient_cab_ben = bt.Inverter()
        seq_tache_ramasser = bt.SequenceStar()
        seq_tache_deposer = bt.SequenceStar()

        inverter_contient_cab_ben.add_child(contient_cab_ben1)
        seq_aller_ramasser.add_child(inverter_contient_cab_ben)
        seq_aller_ramasser.add_child(seq_tache_ramasser)

        seq_aller_deposer.add_child(contient_cab_ben2)
        seq_aller_deposer.add_child(seq_tache_deposer)

        ###--------------------------------------------------
        ###tache ramasser
        ###--------------------------------------------------

        moveto_entrepot = bt_vehicule.MoveToLocation(self, self.noeud_entrepot)
        selector_cab_ben = bt.SelectorStar()

        seq_tache_ramasser.add_child(moveto_entrepot)
        seq_tache_ramasser.add_child(selector_cab_ben)

        #cab
        seq_cab = bt.SequenceStar()
        is_cab = bt_vehicule.IsCabEa(self)
        cab_delay = bt.Delay(60)
        ramasser_cab = bt_vehicule.RamasserCabEa(self)

        cab_delay.add_child(ramasser_cab)
        seq_cab.add_child(is_cab)
        seq_cab.add_child(cab_delay)

        #ben
        seq_ben = bt.SequenceStar()
        is_ben = bt_vehicule.IsBenVide(self)
        ben_delay = bt.Delay(60)
        ramasser_ben = bt_vehicule.RamasserBenVide(self)

        ben_delay.add_child(ramasser_ben)
        seq_ben.add_child(is_ben)
        seq_ben.add_child(ben_delay)

        selector_cab_ben.add_child(seq_cab)
        selector_cab_ben.add_child(seq_ben)

        ###--------------------------------------------------
        ###tache deposer
        ###--------------------------------------------------
        moveto_obj_aller = bt_vehicule.MoveToObjectifAller(self)
        selector_cab_ben = bt.SelectorStar()

        seq_tache_deposer.add_child(moveto_obj_aller)
        seq_tache_deposer.add_child(selector_cab_ben)

        #cab
        seq_cab = bt.SequenceStar()
        is_cab = bt_vehicule.IsCabEa(self)
        cab_delay = bt.Delay(60)
        ramasser_cab = bt_vehicule.DeposerCabEa(self)

        cab_delay.add_child(ramasser_cab)
        seq_cab.add_child(is_cab)
        seq_cab.add_child(cab_delay)

        #ben
        seq_ben = bt.SequenceStar()
        is_ben = bt_vehicule.IsBenVide(self)
        ben_delay = bt.Delay(60)
        ramasser_ben = bt_vehicule.DeposerBenVide(self)

        ben_delay.add_child(ramasser_ben)
        seq_ben.add_child(is_ben)
        seq_ben.add_child(ben_delay)

        selector_cab_ben.add_child(seq_cab)
        selector_cab_ben.add_child(seq_ben)

        #--------------------------------------------------
        #objectif retour
        #--------------------------------------------------

        seq_retour = bt.Sequence()
        obj_retour_existe = bt_vehicule.ObjectifRetourExiste(self)
        repeat_until_success_retour = bt.RepeatUntilSucces()

        seq_retour.add_child(obj_retour_existe)
        seq_retour.add_child(repeat_until_success_retour)

        seq_retour_ramasser_deposer = bt.SequenceStar()
        seq_retour_ramasser = bt.SequenceStar()
        seq_retour_deposer = bt.SequenceStar()

        repeat_until_success_retour.add_child(seq_retour_ramasser_deposer)
        seq_retour_ramasser_deposer.add_child(seq_retour_ramasser)
        seq_retour_ramasser_deposer.add_child(seq_retour_deposer)

        ##--------------------------------------------------
        ##ramasser entrepot cab ea ou ben vide
        ##--------------------------------------------------

        contient_cab_ben1 = bt_vehicule.ContientCabBen(self)
        contient_cab_ben2 = bt_vehicule.ContientCabBen(self)
        inverter_contient_cab_ben = bt.Inverter()
        seq_tache_ramasser = bt.SequenceStar()
        seq_tache_deposer = bt.SequenceStar()

        inverter_contient_cab_ben.add_child(contient_cab_ben1)
        seq_retour_ramasser.add_child(inverter_contient_cab_ben)
        seq_retour_ramasser.add_child(seq_tache_ramasser)

        seq_retour_deposer.add_child(contient_cab_ben2)
        seq_retour_deposer.add_child(seq_tache_deposer)

        ###--------------------------------------------------
        ###tache ramasser
        ###--------------------------------------------------

        moveto_obj_retour = bt_vehicule.MoveToObjectifRetour(self)
        selector_cab_ben = bt.SelectorStar()

        seq_tache_ramasser.add_child(moveto_obj_retour)
        seq_tache_ramasser.add_child(selector_cab_ben)

        #cab
        seq_cab = bt.SequenceStar()
        is_cab = bt_vehicule.IsCabMegot(self)
        cab_delay = bt.Delay(60)
        ramasser_cab = bt_vehicule.RamasserCabMegot(self)

        cab_delay.add_child(ramasser_cab)
        seq_cab.add_child(is_cab)
        seq_cab.add_child(cab_delay)

        #ben
        seq_ben = bt.SequenceStar()
        is_ben = bt_vehicule.IsBenPleine(self)
        ben_delay = bt.Delay(60)
        ramasser_ben = bt_vehicule.RamasserBenPleine(self)

        ben_delay.add_child(ramasser_ben)
        seq_ben.add_child(is_ben)
        seq_ben.add_child(ben_delay)

        selector_cab_ben.add_child(seq_cab)
        selector_cab_ben.add_child(seq_ben)

        ###--------------------------------------------------
        ###tache deposer
        ###--------------------------------------------------
        moveto_entrepot = bt_vehicule.MoveToLocation(self, self.noeud_entrepot)
        selector_cab_ben = bt.SelectorStar()

        seq_tache_deposer.add_child(moveto_entrepot)
        seq_tache_deposer.add_child(selector_cab_ben)

        #cab
        seq_cab = bt.SequenceStar()
        is_cab = bt_vehicule.IsCabMegot(self)
        cab_delay = bt.Delay(60)
        ramasser_cab = bt_vehicule.DeposerCabMegot(self)

        cab_delay.add_child(ramasser_cab)
        seq_cab.add_child(is_cab)
        seq_cab.add_child(cab_delay)

        #ben
        seq_ben = bt.SequenceStar()
        is_ben = bt_vehicule.IsBenPleine(self)
        ben_delay = bt.Delay(60)
        ramasser_ben = bt_vehicule.DeposerBenPleine(self)

        ben_delay.add_child(ramasser_ben)
        seq_ben.add_child(is_ben)
        seq_ben.add_child(ben_delay)

        selector_cab_ben.add_child(seq_cab)
        selector_cab_ben.add_child(seq_ben)

        #############################################

        selector_tache.add_child(seq_aller)
        selector_tache.add_child(seq_retour)
        print(self.root)

class VehiculeCr(ecs.Component):

    def __init__(self, nom, index, mobile=None, entity_manager=None, noeud_entrepot=None):
        self.mobile = mobile
        self.entity_manager = entity_manager
        self.noeuds_entrepot = noeud_entrepot

        self.objectifs = deque()
        self.objectif = None

    def update(self):
        pass

class RenderVehiculeEa(ecs.System):
    """Systeme pour le rendering des box."""
    def __init__(self, canvas,couleurs,textures):
        super().__init__()
        self.canvas=canvas
        self.couleurs=couleurs
        self.textures=textures

    def init(self):
        pass

    def reset(self):
        pass

    def update(self, dt):
        with self.canvas.after:
            for entity, vehicule in self.entity_manager.pairs_for_type(VehiculeEa):
                box = vehicule.mobile.noeud.box
                Rectangle(pos=box.pos, size=box.size)
                Color(0,0,0,1)
                Line(rectangle=box.pos+(12,12))