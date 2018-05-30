"""
Composants reliés à l'horaire d'activité.
-----------------------------------------
"""
from .. import ecs
from . import stochastique

class Horaire(ecs.Component):
    """Horaire de base se répétant a intervalle fixe."""
    def __init__(self, mom, cible, mtags, periode):
        """Configure l'horaire. La var d'état clef est ``actif`` et est dans un composant target. 
        C'est le target qui est responsable de l'initialisation.
        C'est le target qui est responsable de l'initialisation. Cette version de horaire peut 
        être mise-à-jour à la seconde ou à la minute, ça ne change rien car les tags sont en minutes. 

        :param mom: on garde un handle vers le moment
        :type mom: :class:`sim.base.Moment`
        :param cible: un composant target avec la var d'état ``actif``
        :param mtags: la liste de triplet (j,h,m) de changement d'état, j=0 est le jour actuel
        :param periode: un triplet (j,h,m) pour la periode de cycle chaque j jours, h heures et m min
        """
        self.mom=mom # instance de Moment
        self.target=cible # la target avec un horaire (doit avoir une var d'etat actif)
        self.periode=60*(periode[0]*1440+periode[1]*60+periode[2])
        # les tags de changement (en secondes) d'etat de self.target.actif sur 24h
        self.tags=[60*(x[0]*1440+x[1]*60+x[2])-self.mom.t0 for x in mtags]
        self.nextTagIdx=0 # on suppose partir de mom.t0 et que self.tags[0]>mom.t0
        if not self.tags:
            print("Attention! Horaire: Pas de tags")

    def update(self):
        """ Update la var d'état ``actif`` dans le target selon la minute actuelle et les tags."""
        if self.tags and (self.mom.t%self.periode)==self.tags[self.nextTagIdx]:
            self.target.actif=not self.target.actif
            self.nextTagIdx+=1
            if self.nextTagIdx>=len(self.tags): self.nextTagIdx=0


class HoraireSto(ecs.Component):
    """Horaire de base se répétant a intervalle fixe."""
    def __init__(self, mom, cible, mtags, periode, mtbf, mttr, mttrMin=-1, mttrAlpha=-1):
        """Configure l'horaire. La var d'état clef est ``actif`` et est dans un composant target. 
        C'est le target qui est responsable de l'initialisation. Cette version de horaire peut 
        être mise-à-jour à la seconde ou à la minute, ça ne change rien car les tags sont en minutes. 
        Il faut fournir les mtbf et mttr en minutes. 

        Par defaut, la durée d'un bris est fixée à mttf. Cependant, si on donne des valeurs 
        acceptable pour mttrMin et mttrAlpha, on utilise une loi triangulaire. En outre, il 
        faut respecter mttrMin<mttr, 0.0<=mttrAlpha<=1.0. On fixe mttrMode=mttrMin+mttrAlpha*(mttr-mttrMin).
        Ainsi, avec mttrAlpha=0 la loi s'étire au maximum vers les grandes valeurs et avec mttrAlpha=1 
        la loi est centrée symétrique sur la moyenne.

        :param mom: on garde un handle vers le moment
        :type mom: :class:`sim.base.Moment`
        :param cible: un composant target avec la var d'état ``actif``
        :param mtags: la liste de triplet (j,h,m) de changement d'état, j=0 est le jour actuel
        :param periode: un triplet (j,h,m) pour la periode de cycle chaque j jours, h heures et m min
        :param mtbf: mean time b4 failure en minutes wallclock
        :param mttr: mean time to repair en minutes wallclock
        :param mttrMin: mttr min pour loi triangulaire
        :param mttrAlpha: facteur dans [0,1] pour le décentrement de la loi triangulaire (1=centré)
        """
        self.mom=mom # instance de Moment
        self.target=cible # la target avec un horaire (doit avoir une var d'etat actif)
        self.periode=60*(periode[0]*1440+periode[1]*60+periode[2])
        # les tags de changement (en secondes) d'etat de self.target.actif sur 24h
        self.tags=[60*(x[0]*1440+x[1]*60+x[2])-self.mom.t0 for x in mtags]
        self.nextTagIdx=0 # on suppose partir de mom.t0 et que self.tags[0]>mom.t0
        # partie stochastique
        self.triggerFreq=stochastique.TriggerFrequence(1.0/mtbf)
        self.mttr=stochastique.ConstantValue(mttr)
        if 0<mttrMin and mttrMin<mttr and 0<=mttrAlpha and mttrAlpha<=1:
            mttrMode=(int)(mttrMin+mttrAlpha*(mttr-mttrMin))
            mttrMax=3*mttr-mttrMin-mttrMode
            if mttr<mttrMax:
                print("HoraireSto avec loi triangulaire (min,mode,moy,max)=",mttrMin,mttrMode,mttr,mttrMax)
                self.mttr=stochastique.TriangularDistributionSample(mttrMin,mttrMax,mttrMode)
        self.actif_horaire=self.target.actif # set l'etat horaire selon le target
        self.duree_arret=0 # en minute
        self.new_trigger=False

    def update(self):
        """ Update la var d'état ``actif`` dans le target selon la minute actuelle et les tags."""
        self.new_trigger=False
        if self.nextTagIdx>=len(self.tags):
            pass # pas de tag, donc pas de changement d'etat
            #print("Erreur HoraireJour: Pas de tags")
        elif (self.mom.t%self.periode)==self.tags[self.nextTagIdx]:
            self.actif_horaire=not self.actif_horaire # etat de l'horaire
            self.nextTagIdx+=1
            if self.nextTagIdx>=len(self.tags): self.nextTagIdx=0
        if self.mom.tickM: # tick a la minute
            self.duree_arret-=1 
            if self.triggerFreq.get(): 
                self.new_trigger=True
                #print("  *** trigger!",self.mom.getJHMS())
                self.duree_arret=self.mttr.get()
            #if self.duree_arret==1: print("  === fin trigger!",self.mom.getJHMS())
        if self.duree_arret>0: self.target.actif=False
        else: self.target.actif=self.actif_horaire
        

class HoraireStoTAP(ecs.Component):
    """Horaire stochastique special pour une TAP, avec répétition."""
    def __init__(self, mom, cible, mtags, periode, arretplan, freq=None, arretnonplan=None):
        """Configure l'horaire. La var d'état clef est ``actif`` et est dans un composant target. 
        On force l'initialisation a True. Les tags imposent les debuts des arrets planifies.

        :param mom: on garde un handle vers l'entité père
        :type mom: :class:`sim.base.Moment`
        :param cible: un composant target avec la var d'état ``actif``
        :param mtags: la liste de triplet (j,h,m) de changement d'état, j=0 est le jour actuel
        :param periode: un triplet (j,h,m) pour la periode de cycle chaque j jours, h heures et m min
        :param arretplan: est un objet avec la methode ``get`` pour obtenir la duree des arrets dans mtags (en secondes)
        :param freq: est un objet qui trigger un arrets non-planifies
        :param arretnonplan: est un objet avec la methode ``get`` pour obtenir la duree des arrets non-planifies genere via freq (en secondes)
        """
        self.mom=mom # instance de Moment
        self.target=cible # la target avec un horaire (doit avoir une var d'etat actif)
        self.periode=60*(periode[0]*1440+periode[1]*60+periode[2])
        # les tags de changement (en secondes) d'etat de self.target.actif sur 24h
        self.tags=[60*(x[0]*1440+x[1]*60+x[2])-self.mom.t0 for x in mtags]
        self.nextTagIdx=0 # on suppose partir de mom.t0 et que self.tags[0]>mom.t0
        self.arretplan=arretplan # objet avec methode get de la duree d'un arret plan
        self.freq=freq # objet frequence avec methode get de trigger d'un arret non-plan
        self.arretnonplan=arretnonplan # objet avec methode get de la duree d'un arret non-plan
        self.target.actif=True # init a True
        self.duree=-1 # duree de l'arret en cours
        self.trigger=False # trigger d'un arret non-plan

    def update(self):
        """ Update la var d'état ``actif`` dans le target selon la minute actuelle et les tags."""
        if self.freq is not None and not self.trigger: 
            self.trigger=self.freq.get() # test de trigger d'un arret nonplan, si on en a pas deja un
        self.duree-=1 # decroit la duree d'un arret
        if self.nextTagIdx>=len(self.tags):
            print("Erreur HoraireStoTAP: Pas de tags")
        elif (self.mom.t%self.periode)==self.tags[self.nextTagIdx]: # debut d'un arret planifie
            self.duree=self.arretplan.get() # duree stochastique de l'arret planifie
            #print("Arret planifie (sec):",self.duree)
            self.nextTagIdx+=1
            if self.nextTagIdx>=len(self.tags): self.nextTagIdx=0
        if self.duree<=0 and self.trigger: # si pas en arret, mais qu'on a un trigger d'arret nonplan
            self.duree=self.arretnonplan.get() # duree de l'arret nonplan
            #print("  Arret non-planifie (sec):",self.duree)
            self.trigger=False # reset du trigger
        # cas special pour entrepot plein (on suppose qu'on a un handle sur l'entrepot)
        # le handle doit etre mis dans modele
        if self.duree<=0 and not self.entrepot.place4crue():
            self.duree=24*3600 # pause de 48h (entrepot plein) (update 28 oct: 24h)
            #print(self.mom.getJHMS()," Pause TAP pour 48h car entrepot plein, duree de (sec)",self.duree)
        # update de actif
        if self.duree>0: self.target.actif=False # si en arret, alors non actif
        else: self.target.actif=True


class HoraireJour(ecs.Component):
    """Horaire de base pour une journée (24h), se répétant. ATTENTION: desuet et non-supporte. """
    def __init__(self, mom, cible, mtags):
        """Configure l'horaire. La var d'état clef est ``actif`` et est dans un composant target. 
        C'est le target qui est responsable de l'initialisation.

        :param mom: on garde un handle vers l'entité père
        :type mom: :class:`sim.base.Moment`
        :param cible: un composant target avec la var d'état ``actif``
        :param mtags: la liste de minutes de changement d'état, des entiers entre 0-1439
        """
        self.mom=mom # instance de Moment
        self.target=cible # la target avec un horaire (doit avoir une var d'etat actif)
        # les tags de changement (en secondes) d'etat de self.target.actif sur 24h
        self.tags=[x*60 for x in mtags]
        self.nextTagIdx=0 # on suppose partir de mom.t0 et que self.tags[0]>mom.t0

    def update(self):
        """ Update la var d'état ``actif`` dans le target selon la minute actuelle et les tags."""
        if self.nextTagIdx>=len(self.tags):
            print("Erreur HoraireJour: Pas de tags")
        elif self.mom.tnow==self.tags[self.nextTagIdx]:
            self.target.actif=not self.target.actif
            self.nextTagIdx+=1
            if self.nextTagIdx>=len(self.tags): self.nextTagIdx=0


