"""
Utilitaires de base pour la simulation.
---------------------------------------
"""
import csv
import math
import datetime
from collections import OrderedDict, defaultdict, namedtuple


class Pheromone:
    """ Une phéromone est en fait un spot pour avoir une phéromone active.
        C'est une condition True a l'update de l'état du spot qui renforce ou crée
        la phéromone en tant que telle.

        Exemple d'utilisation:

    .. code-block:: python

        p = base.Pheromone(60)
        for i in range(600):
            p.update(i==50 or i==150 or i==180)
        p.show()

    """

    def __init__(self,vie):
        """Création de la phéromone non-active. C'est l'update avec une variable qui l'active
        ou la tiens en vie. Après vie unités de temps sans reactivation, elle se déactive.
        D'un point de vue, l'objet est plutôt un spot pour recevoir une phéromone.

        :param vie: durée de vie en unité de temps selon update
        """
        self.vie=vie # parametre de vie lors de l'activation
        self._vieRestante = 0 # tracking de la sante, i.e. dissipation de la pheromone
        self.dt = 0 # duree de vie totale (age) de la pheromone courante
        # statistiques
        self.n = 0 # stat du nb de phéromones distinctes
        self.dtmoy = 0 # duree de vie moyenne d'une pheromone
        self.dtmax = 0 # duree de vie max d'une pheromone

    def _emettre(self):
        """ Emettre une nouvelle phéromone ou reforcer une existante. """
        if self._vieRestante == 0: self.n += 1 # on emet une nouvelle
        elif self._vieRestante>0:
            self.dt+=self.vie-self._vieRestante # on update l'age
        self._vieRestante = self.vie # dans tous les cas, on fixe la vie restante a vie

    def update(self,depot=False):
        """ Update (dissipation) de l'état de la phéromone.

        :param depot: si vrai on emet ou renforce une phéromone
        """
        if self._vieRestante > 0:
            self._vieRestante -= 1
            if self._vieRestante == 0: # viens de mourrir...
                self.dt+=self.vie
                if self.dt>self.dtmax: self.dtmax=self.dt
                self.dtmoy = ((self.n-1)*self.dtmoy+self.dt)/self.n
                self.dt=0 # reset de la duree de vie totale
        if depot: self._emettre()

    def show(self):
        """ Print les stats. """
        print("n",self.n,"age moy",self.dtmoy,"age max",self.dtmax)


class Monitor:
    """ Cette classe gère une liste de données à meme la classe. C'est-à-dire que
    la liste est un attribut de classe et non d'objet. Typiquement, le but est d'offrir
    un mécanisme simple et léger pour collecter une trace globale d'exécution qu'on
    peut afficher ou consulter avec un chiffrier. On suppose que chaque donnée est
    un tuple structurée comme une ligne csv. Toute les méthodes sont statiques.

    Exemple d'utilisation pour une entête et lignes de données:

    .. code-block:: python

        base.Monitor.add( ("Heure","X","Y") ) # ligne d'entete
        base.Monitor.add( ("20h15",3,13) ) # premiere ligne de data
        base.Monitor.add( ("21h35",4,19) ) # seconde ligne de data
        base.Monitor.show() # affichage a l'ecran
        base.Monitor.dump() # dump dans datadex.csv avec ; comme separateur

    """

    _datadex = [] # les donnees

    @staticmethod
    def add(data):
        """ Ajoute une ligne de données dans la liste du monitor. """
        Monitor._datadex.append(data)

    @staticmethod
    def show():
        """ Affiche a l'écran toutes les lignes de données du monitor. """
        for data in Monitor._datadex:
            print(data)

    @staticmethod
    def dump():
        """ Dump dans datadex.csv avec ; comme séparateur. """
        with open('datadex.csv', 'a', newline='') as fp:
            z = csv.writer(fp, delimiter=';')
            z.writerows(Monitor._datadex)


class Debug:
    """ Permet de print un message concernant un obj lorsque le
        flag `is_debug` existe dans l'objet cible.

        Exemple d'utilisation:

    .. code-block:: python

        base.Debug.set_debug_print_on(obj)
        base.Debug.print(obj, "Le flag is_debug est dans l'objet obj")
    """

    @staticmethod
    def set_debug_print_on(obj):
        """Insert l'attribut `is_debug` dans l'objet cible.

        :param obj: objet cible
        """
        obj.is_debug = True

    @staticmethod
    def set_debug_print_off(obj):
        """Delete l'attribut `is_debug` dans l'objet cible.

        :param obj: objet cible
        """
        delattr(obj, 'is_debug')

    @staticmethod
    def is_debug_print(obj):
        """Détermine si l'attribut 'is_debug' existe dans l'objet cible.

        :param obj: objet cible
        """
        return 'is_debug' in dir(obj)

    @staticmethod
    def print(obj, *args):
        """Print un message contenu dans 'args'

        :param obj: objet cible
        :param args: message à print
        """
        if Debug.is_debug_print(obj):
            print(*args)


class Blackboard:
    """Simple blackboard (bb) to store shared information. On crée des entrées dans le
       bb en y insérant des valeurs directement ou avec `set`. On peut retrouver et
       modifier les valeur directement, mais il est préférable d'utiliser `set` et `get`
       car ils s'assurent que l'attribut est bien présent dans le bb.

       Exemple d'utilisation:

    .. code-block:: python

       bb=simulation.base.Blackboard()
       bb.x=2
       bb.set('y',3)
    """

    def show_content(self):
        """Liste du contenu du bb excluant les items privés (i.e. contenant ``__``)."""
        print([x for x in dir(self) if x.find('__') < 0])

    def delete(self, attr):
        """Delete l'attribut `attr` du blackboard.

        :param attr: nom de l'attribut à retirer (une string)
        """
        if attr in dir(self): delattr(self, attr)

    def get(self, attr):
        """Get la valeur de l'attribut `attr` en s'assurant qu'il
           existe dans le blackboard.

        :param attr: nom de l'attribut à retrouver
        """
        return getattr(self, attr)

    def set(self, attr, value):
        """Set la valeur de l'attribut `attr` à `value` en s'assurant qu'il
           existe dans le blackboard.

        :param attr: nom de l'attribut à retrouver (une string)
        :param value: valeur à affecter à l'attribut
        """
        setattr(self, attr, value)

    def has(self, attr):
        """Test si l'object blackboard possède l'attribut `attr`.

        :param attr: nom de l'attribut à rechercher (une string)
        """
        return attr in dir(self)


class Publisher:
    """Déclenche un événement chez les subscribers lorsque un message est reçu. """

    instance = None

    @staticmethod
    def get_instance():
        """Recupère l'instance unique du publisher, crée l'instance lorsqu'elle n'existe pas.

        """
        if Publisher.instance is None:
            Publisher.instance = Publisher()
        return Publisher.instance

    def __init__(self):
        self.events = defaultdict(lambda: defaultdict())

    def get_subscribers(self, event):
        """Retourne les subscribers inscrit à 'event'

        :param event: nom de l'event (une string)
        """
        return self.events[event]

    def register(self, event, who, callback=None):
        """Enregistre 'who' à l'événement 'event' celui-ci appelera la fonction 'callback' lorsque déchlenché.

        :param event: nom de l'événement (une string)
        :param who: l'objet inscrit à l'événement
        :param callback: fonction à déclencher, par défaut 'notify()'
        """
        if callback is None:
            callback = getattr(who, 'notify')
        self.get_subscribers(event)[who] = callback

    def unregister(self, event, who):
        """Retire 'who' de l'événement 'event'

        :param event: nom de l'événement (une string)
        :param who: l'objet inscrit à l'événement
        """
        del self.get_subscribers(event)[who]

    def dispatch(self, event, sender, message):
        """Déclenche l'évenement 'event' envoit un message (peut être un objet)

        :param event: nom de l'événement (une string)
        :param sender: objet déclencher de l'événement
        :param message: message à envoyer (peut être un objet)
        """
        for subscriber, callback in self.get_subscribers(event).items():
            callback(subscriber, sender, message)


class TripleManager:
    """Provide database-like access to triple based on a key: (object,property)."""

    def __init__(self,interpreteCF=False):
        """Creation de 2 dictionnaires utilisant une clé (object,property).
        Un est pour les valeurs, l'autre pour des commentaires. On peut interpréter
        un commentaire comme un facteur de confiance dans [-1,1]. Dans ce cas,
        le dictionnaire de commentaire contient le facteur de confiance.
        """
        self.interpreteCF = interpreteCF # active l'interprétation des comments comme CF
        self._bdv = OrderedDict()  # values for (object,property) pairs
        self._bdc = OrderedDict()  # comments or CF for (object,property) pairs

    def add(self, anobject, aproperty, avalue, acomment=""):
        """Add a triple to the database: (anobject,aproperty,avalue) and acomment or CF.
        Si la clef existe déjà, on remplace le contenu par le plus récent.
        Il est recommandé d'utiliser getv pour tester si la clef existe lorsque c'est utile.
        Par convention, on traite les étoiles comme des separateurs pour generer des tuples d'entiers.
        Exemple: '23*-40' devient le couple (23,-40).

        :param anobject: premier membre du couple de la clé
        :param aproperty: second membre du couple de la clé
        :param avalue: item a mettre dans le dictionnaire des valeurs
        :param acomment: texte optionnel ou CF a mettre dans le dictionnaire des commentaires

        Les types sont arbitraires, par exemple ``avalue`` peut être un objet, un tuple, etc.
        """
        if isinstance(avalue, str) and avalue.find('*') >= 0:
            try:
                avalue = tuple(int(i) for i in avalue.split('*'))
            except ValueError:
                avalue = tuple(str(i) for i in avalue.split('*'))

        self._bdv[(anobject, aproperty)] = avalue
        if self.interpreteCF:
            if not isinstance(acomment,float): acomment=1.0
        self._bdc[(anobject, aproperty)] = acomment

    def getv(self, pair):
        """Return la valeur associée à la clé

        :param pair: couple (objet,propriete) qui est une clé de la bd des valeurs
        :return: la valeur associée à la clé
        :rtype: quelconque ou None si pas dans le dict
        """
        try:
            return self._bdv[pair]
        except KeyError:
            return None

    def getc(self, pair):
        """Return le commentaire associé à la clé

        :param pair: couple (objet,propriete) qui est une clé de la bd des commentaires
        :return: le commentaire associé à la clé
        :rtype: une string ou None si pas dans le dict
        """
        try:
            return self._bdc[pair]
        except KeyError:
            return None

    def to_blackboard(self):
        def num(s):
            try:
                return int(s)
            except ValueError:
                try:
                    return float(s)
                except ValueError:
                    return s
            except TypeError:
                return s

        root_bb = Blackboard()

        for k in self._bdv:
            key0 = k[0].replace('-', '_')
            key1 = k[1].replace('-', '_')
            if root_bb.has(key0):
                bb = root_bb.get(key0)
                bb.set(key1, num(self.getv(k)))
                root_bb.set(key0, bb)
            else:
                bb = Blackboard()
                bb.set(key1, num(self.getv(k)))
                root_bb.set(key0, bb)
        return root_bb

    def load(self, nom, bypass_title_line_one=True):
        """Load la BD des valeurs et des commentaires via le fichier csv ``nom``."""
        with open(nom, newline='') as csvfile:
            dat = csv.reader(csvfile, delimiter=';', quotechar='|')
            if bypass_title_line_one:
                dat.__next__()  # saute la premiere ligne (les titres)
            for row in dat:
                if len(row) > 2:
                    acomment=row[3]
                    if self.interpreteCF:
                        try:
                            acomment=float(row[3])
                        except:
                            acomment=1.0
                    self.add(row[0], row[1], row[2], acomment)

    def dump(self):
        """Dump la BD des valeurs et des commentaires dans le fichier csv ``dump.csv``.
        On y trouve les entrées initiales et celles ajoutées. L'ordre est arbitraire.
        Rien ne garantie que load(dump()) reconstruit correctement. En fait, les tuples
        ne sont pas reconvertis avec des * et les nombres sont mis en string. """
        with open('dump.csv', 'w', newline='') as fp:
            a = csv.writer(fp, delimiter=';')
            data = []
            for k in self._bdv:
                li = [k[0], k[1]]
                li.append(self.getv(k))
                li.append(self.getc(k))
                data.append(li)
            a.writerows(data)

    def show(self):
        """Dump la BD des valeurs et des commentaires a la sortie standard."""
        for k in self._bdv:
            li = [k[0], k[1]]
            li.append(self.getv(k))
            li.append(self.getc(k))
            print(li)


class Moment:
    """Gestionnaire de temps en système 24 heures."""
    instance = None

    def __init__(self, t0):
        """Cree une instance du gestionnaire de temps. A priori, il doit être unique.

        :param int t0: seconde de référence d'une journée d'opération, exemple: 7*60*60 pour 7h.
        """
        self.dt = 1  # pas de temps en seconde
        self.t0 = t0  # heure de reference du depart en secondes
        self.t = 0  # nombre de seconde brut (principale variable d'etat)
        self.tnow = t0  # t now (somme de t0 et t) module 24h
        self.trel = 0 # t module 12h (temps relatif au quart en cours)
        self.ticks_reset()  # reset des ticks

        self.nbHeureQuart = 12
        self.set_instance()

    def set_instance(self):
        if Moment.instance is None:
            Moment.instance = self

    @staticmethod
    def get_instance():
        if Moment.instance is not None:
            return Moment.instance
        else:
            Moment.instance = Moment(0)
            return Moment.instance

    def update(self):
        """Avance de dt dans le temps et update des variables associees."""
        self.t += self.dt
        self.tnow = (self.t0 + self.t) % 86400
        self.trel = self.t % 43200
        self.ticks_reset()
        self.ticks_set()

    def ticks_reset(self):
        """Reset des ticks."""
        self.tickQ = False  # quart
        self.tickM = False  # minute
        self.tickH = False  # heure
        self.tickJ = False  # jour

    def ticks_set(self):
        """Activation des ticks. Un tick est True durant une seconde selon la fréquence
        d'activation. Les principaux tick disponibles sont:

            * tickQ: activation à chaque quart (de 12 heures)
            * tickM: activation à chaque minute
            * tickH: activation à chaque heure
            * tickJ: activation à chaque jour
        """
        self.tickQ = self.t % 43200 == 0
        self.tickM = self.t % 60 == 0
        self.tickH = self.t % 3600 == 0
        self.tickJ = self.t % 86400 == 0

    def nbj(self):
        """ Nb de jours depuis le debut de la simulation. """
        return self.t//86400

    def getJHMS(self):
        """Transforme le temps interne en jour h:m:s tenant compte du t0 de référence.

        :return: une string en format jour:heure:min:sec
        """
        x = self.t0 + self.t
        q = self.t // 43200
        h = x // 3600
        j = h // 24
        h = h % 24
        x = x - j * 86400
        h = x // 3600  # heure du jour
        s = x % 3600  # secondes restantes
        m = s // 60
        s = s % 60
        #d = 'D' if 7 <= h < 19 else 'N'

        return '{0:02d}j{1:02d}h{2:02d}m{3:02d}s ({4})'.format(j, h, m, s, q+1)

    @staticmethod
    def seconds_to_hhmmss(seconds):
        h = seconds // 3600
        s = seconds % 3600
        m = s // 60
        s = s % 60
        return '{0:02d}h{1:02d}m{2:02d}s'.format(h, m, s)

    def get_t_as_hhmmss(self):
        return Moment.seconds_to_hhmmss(self.t)

class MomentRT:
    """ Gestionnaire de temps real-time. """

    def __init__(self, _dt):
        """Cree une instance du gestionnaire de temps RT.

        :param int _dt: nb de secondes RT pour trigger elapsed.
        """
        self.dt = datetime.timedelta(0,_dt)  # delta de temps RT en seconde
        # temps de reference du trigger precedent (init a now-180jours)
        self.stamp = datetime.datetime.now()-datetime.timedelta(180)

    def elapsed(self):
        """True si dt secondes RT ce sont passées depuis le dernier appel."""
        e=datetime.datetime.now()-self.stamp
        if e.total_seconds()>=30:
            self.stamp = datetime.datetime.now()
            return True
        else:
            return False


class Vecteur2D:
    @staticmethod
    def proj(a, b):
        d = Vecteur2D.dot(a, b)
        m = Vecteur2D.mag(b)
        t = d / m
        return t, (t * b[0], t * b[1])

    @staticmethod
    def comp(a, b):
        d = Vecteur2D.dot(a, b)
        m = Vecteur2D.mag(a)
        return d / m

    @staticmethod
    def magsqrt(a):
        return math.sqrt(a[0] * a[0] + a[1] * a[1])

    @staticmethod
    def mag(a):
        return a[0] * a[0] + a[1] * a[1]

    @staticmethod
    def sub(a, b):
        return a[0] - b[0], a[1] - b[1]

    @staticmethod
    def add(a, b):
        return a[0] + b[0], a[1] + b[1]

    @staticmethod
    def dist(a, b):
        d = Vecteur2D.sub(a, b)
        return d[0] * d[0] + d[1] * d[1]

    @staticmethod
    def distsqrt(a, b):
        return math.sqrt(Vecteur2D.dist(a, b))

    @staticmethod
    def dot(a, b):
        return a[0] * b[0] + a[1] * b[1]


class Math:
    @staticmethod
    def safe_scalar_div(x, y):
        if y == 0:
            return 0
        return x / y

    @staticmethod
    def clamp(n, smallest, largest):
        return max(smallest, min(n, largest))


class RGB(namedtuple('RGB', 'r, g, b')):

    @staticmethod
    def rgb_to_float(r, g, b):
        return r/255.0, g/255.0, b/255.0

    def to_float(self):
        return self.r/255.0, self.g/255.0, self.b/255.0

class Palette():
    # Color Contants
    ALICEBLUE = RGB(240, 248, 255)
    ANTIQUEWHITE = RGB(250, 235, 215)
    ANTIQUEWHITE1 = RGB(255, 239, 219)
    ANTIQUEWHITE2 = RGB(238, 223, 204)
    ANTIQUEWHITE3 = RGB(205, 192, 176)
    ANTIQUEWHITE4 = RGB(139, 131, 120)
    AQUA = RGB(0, 255, 255)
    AQUAMARINE1 = RGB(127, 255, 212)
    AQUAMARINE2 = RGB(118, 238, 198)
    AQUAMARINE3 = RGB(102, 205, 170)
    AQUAMARINE4 = RGB(69, 139, 116)
    AZURE1 = RGB(240, 255, 255)
    AZURE2 = RGB(224, 238, 238)
    AZURE3 = RGB(193, 205, 205)
    AZURE4 = RGB(131, 139, 139)
    BANANA = RGB(227, 207, 87)
    BEIGE = RGB(245, 245, 220)
    BISQUE1 = RGB(255, 228, 196)
    BISQUE2 = RGB(238, 213, 183)
    BISQUE3 = RGB(205, 183, 158)
    BISQUE4 = RGB(139, 125, 107)
    BLACK = RGB(0, 0, 0)
    BLANCHEDALMOND = RGB(255, 235, 205)
    BLUE = RGB(0, 0, 255)
    BLUE2 = RGB(0, 0, 238)
    BLUE3 = RGB(0, 0, 205)
    BLUE4 = RGB(0, 0, 139)
    BLUEVIOLET = RGB(138, 43, 226)
    BRICK = RGB(156, 102, 31)
    BROWN = RGB(165, 42, 42)
    BROWN1 = RGB(255, 64, 64)
    BROWN2 = RGB(238, 59, 59)
    BROWN3 = RGB(205, 51, 51)
    BROWN4 = RGB(139, 35, 35)
    BURLYWOOD = RGB(222, 184, 135)
    BURLYWOOD1 = RGB(255, 211, 155)
    BURLYWOOD2 = RGB(238, 197, 145)
    BURLYWOOD3 = RGB(205, 170, 125)
    BURLYWOOD4 = RGB(139, 115, 85)
    BURNTSIENNA = RGB(138, 54, 15)
    BURNTUMBER = RGB(138, 51, 36)
    CADETBLUE = RGB(95, 158, 160)
    CADETBLUE1 = RGB(152, 245, 255)
    CADETBLUE2 = RGB(142, 229, 238)
    CADETBLUE3 = RGB(122, 197, 205)
    CADETBLUE4 = RGB(83, 134, 139)
    CADMIUMORANGE = RGB(255, 97, 3)
    CADMIUMYELLOW = RGB(255, 153, 18)
    CARROT = RGB(237, 145, 33)
    CHARTREUSE1 = RGB(127, 255, 0)
    CHARTREUSE2 = RGB(118, 238, 0)
    CHARTREUSE3 = RGB(102, 205, 0)
    CHARTREUSE4 = RGB(69, 139, 0)
    CHOCOLATE = RGB(210, 105, 30)
    CHOCOLATE1 = RGB(255, 127, 36)
    CHOCOLATE2 = RGB(238, 118, 33)
    CHOCOLATE3 = RGB(205, 102, 29)
    CHOCOLATE4 = RGB(139, 69, 19)
    COBALT = RGB(61, 89, 171)
    COBALTGREEN = RGB(61, 145, 64)
    COLDGREY = RGB(128, 138, 135)
    CORAL = RGB(255, 127, 80)
    CORAL1 = RGB(255, 114, 86)
    CORAL2 = RGB(238, 106, 80)
    CORAL3 = RGB(205, 91, 69)
    CORAL4 = RGB(139, 62, 47)
    CORNFLOWERBLUE = RGB(100, 149, 237)
    CORNSILK1 = RGB(255, 248, 220)
    CORNSILK2 = RGB(238, 232, 205)
    CORNSILK3 = RGB(205, 200, 177)
    CORNSILK4 = RGB(139, 136, 120)
    CRIMSON = RGB(220, 20, 60)
    CYAN2 = RGB(0, 238, 238)
    CYAN3 = RGB(0, 205, 205)
    CYAN4 = RGB(0, 139, 139)
    DARKGOLDENROD = RGB(184, 134, 11)
    DARKGOLDENROD1 = RGB(255, 185, 15)
    DARKGOLDENROD2 = RGB(238, 173, 14)
    DARKGOLDENROD3 = RGB(205, 149, 12)
    DARKGOLDENROD4 = RGB(139, 101, 8)
    DARKGRAY = RGB(169, 169, 169)
    DARKGREEN = RGB(0, 100, 0)
    DARKKHAKI = RGB(189, 183, 107)
    DARKOLIVEGREEN = RGB(85, 107, 47)
    DARKOLIVEGREEN1 = RGB(202, 255, 112)
    DARKOLIVEGREEN2 = RGB(188, 238, 104)
    DARKOLIVEGREEN3 = RGB(162, 205, 90)
    DARKOLIVEGREEN4 = RGB(110, 139, 61)
    DARKORANGE = RGB(255, 140, 0)
    DARKORANGE1 = RGB(255, 127, 0)
    DARKORANGE2 = RGB(238, 118, 0)
    DARKORANGE3 = RGB(205, 102, 0)
    DARKORANGE4 = RGB(139, 69, 0)
    DARKORCHID = RGB(153, 50, 204)
    DARKORCHID1 = RGB(191, 62, 255)
    DARKORCHID2 = RGB(178, 58, 238)
    DARKORCHID3 = RGB(154, 50, 205)
    DARKORCHID4 = RGB(104, 34, 139)
    DARKSALMON = RGB(233, 150, 122)
    DARKSEAGREEN = RGB(143, 188, 143)
    DARKSEAGREEN1 = RGB(193, 255, 193)
    DARKSEAGREEN2 = RGB(180, 238, 180)
    DARKSEAGREEN3 = RGB(155, 205, 155)
    DARKSEAGREEN4 = RGB(105, 139, 105)
    DARKSLATEBLUE = RGB(72, 61, 139)
    DARKSLATEGRAY = RGB(47, 79, 79)
    DARKSLATEGRAY1 = RGB(151, 255, 255)
    DARKSLATEGRAY2 = RGB(141, 238, 238)
    DARKSLATEGRAY3 = RGB(121, 205, 205)
    DARKSLATEGRAY4 = RGB(82, 139, 139)
    DARKTURQUOISE = RGB(0, 206, 209)
    DARKVIOLET = RGB(148, 0, 211)
    DEEPPINK1 = RGB(255, 20, 147)
    DEEPPINK2 = RGB(238, 18, 137)
    DEEPPINK3 = RGB(205, 16, 118)
    DEEPPINK4 = RGB(139, 10, 80)
    DEEPSKYBLUE1 = RGB(0, 191, 255)
    DEEPSKYBLUE2 = RGB(0, 178, 238)
    DEEPSKYBLUE3 = RGB(0, 154, 205)
    DEEPSKYBLUE4 = RGB(0, 104, 139)
    DIMGRAY = RGB(105, 105, 105)
    DIMGRAY = RGB(105, 105, 105)
    DODGERBLUE1 = RGB(30, 144, 255)
    DODGERBLUE2 = RGB(28, 134, 238)
    DODGERBLUE3 = RGB(24, 116, 205)
    DODGERBLUE4 = RGB(16, 78, 139)
    EGGSHELL = RGB(252, 230, 201)
    EMERALDGREEN = RGB(0, 201, 87)
    FIREBRICK = RGB(178, 34, 34)
    FIREBRICK1 = RGB(255, 48, 48)
    FIREBRICK2 = RGB(238, 44, 44)
    FIREBRICK3 = RGB(205, 38, 38)
    FIREBRICK4 = RGB(139, 26, 26)
    FLESH = RGB(255, 125, 64)
    FLORALWHITE = RGB(255, 250, 240)
    FORESTGREEN = RGB(34, 139, 34)
    GAINSBORO = RGB(220, 220, 220)
    GHOSTWHITE = RGB(248, 248, 255)
    GOLD1 = RGB(255, 215, 0)
    GOLD2 = RGB(238, 201, 0)
    GOLD3 = RGB(205, 173, 0)
    GOLD4 = RGB(139, 117, 0)
    GOLDENROD = RGB(218, 165, 32)
    GOLDENROD1 = RGB(255, 193, 37)
    GOLDENROD2 = RGB(238, 180, 34)
    GOLDENROD3 = RGB(205, 155, 29)
    GOLDENROD4 = RGB(139, 105, 20)
    GRAY = RGB(128, 128, 128)
    GRAY1 = RGB(3, 3, 3)
    GRAY10 = RGB(26, 26, 26)
    GRAY11 = RGB(28, 28, 28)
    GRAY12 = RGB(31, 31, 31)
    GRAY13 = RGB(33, 33, 33)
    GRAY14 = RGB(36, 36, 36)
    GRAY15 = RGB(38, 38, 38)
    GRAY16 = RGB(41, 41, 41)
    GRAY17 = RGB(43, 43, 43)
    GRAY18 = RGB(46, 46, 46)
    GRAY19 = RGB(48, 48, 48)
    GRAY2 = RGB(5, 5, 5)
    GRAY20 = RGB(51, 51, 51)
    GRAY21 = RGB(54, 54, 54)
    GRAY22 = RGB(56, 56, 56)
    GRAY23 = RGB(59, 59, 59)
    GRAY24 = RGB(61, 61, 61)
    GRAY25 = RGB(64, 64, 64)
    GRAY26 = RGB(66, 66, 66)
    GRAY27 = RGB(69, 69, 69)
    GRAY28 = RGB(71, 71, 71)
    GRAY29 = RGB(74, 74, 74)
    GRAY3 = RGB(8, 8, 8)
    GRAY30 = RGB(77, 77, 77)
    GRAY31 = RGB(79, 79, 79)
    GRAY32 = RGB(82, 82, 82)
    GRAY33 = RGB(84, 84, 84)
    GRAY34 = RGB(87, 87, 87)
    GRAY35 = RGB(89, 89, 89)
    GRAY36 = RGB(92, 92, 92)
    GRAY37 = RGB(94, 94, 94)
    GRAY38 = RGB(97, 97, 97)
    GRAY39 = RGB(99, 99, 99)
    GRAY4 = RGB(10, 10, 10)
    GRAY40 = RGB(102, 102, 102)
    GRAY42 = RGB(107, 107, 107)
    GRAY43 = RGB(110, 110, 110)
    GRAY44 = RGB(112, 112, 112)
    GRAY45 = RGB(115, 115, 115)
    GRAY46 = RGB(117, 117, 117)
    GRAY47 = RGB(120, 120, 120)
    GRAY48 = RGB(122, 122, 122)
    GRAY49 = RGB(125, 125, 125)
    GRAY5 = RGB(13, 13, 13)
    GRAY50 = RGB(127, 127, 127)
    GRAY51 = RGB(130, 130, 130)
    GRAY52 = RGB(133, 133, 133)
    GRAY53 = RGB(135, 135, 135)
    GRAY54 = RGB(138, 138, 138)
    GRAY55 = RGB(140, 140, 140)
    GRAY56 = RGB(143, 143, 143)
    GRAY57 = RGB(145, 145, 145)
    GRAY58 = RGB(148, 148, 148)
    GRAY59 = RGB(150, 150, 150)
    GRAY6 = RGB(15, 15, 15)
    GRAY60 = RGB(153, 153, 153)
    GRAY61 = RGB(156, 156, 156)
    GRAY62 = RGB(158, 158, 158)
    GRAY63 = RGB(161, 161, 161)
    GRAY64 = RGB(163, 163, 163)
    GRAY65 = RGB(166, 166, 166)
    GRAY66 = RGB(168, 168, 168)
    GRAY67 = RGB(171, 171, 171)
    GRAY68 = RGB(173, 173, 173)
    GRAY69 = RGB(176, 176, 176)
    GRAY7 = RGB(18, 18, 18)
    GRAY70 = RGB(179, 179, 179)
    GRAY71 = RGB(181, 181, 181)
    GRAY72 = RGB(184, 184, 184)
    GRAY73 = RGB(186, 186, 186)
    GRAY74 = RGB(189, 189, 189)
    GRAY75 = RGB(191, 191, 191)
    GRAY76 = RGB(194, 194, 194)
    GRAY77 = RGB(196, 196, 196)
    GRAY78 = RGB(199, 199, 199)
    GRAY79 = RGB(201, 201, 201)
    GRAY8 = RGB(20, 20, 20)
    GRAY80 = RGB(204, 204, 204)
    GRAY81 = RGB(207, 207, 207)
    GRAY82 = RGB(209, 209, 209)
    GRAY83 = RGB(212, 212, 212)
    GRAY84 = RGB(214, 214, 214)
    GRAY85 = RGB(217, 217, 217)
    GRAY86 = RGB(219, 219, 219)
    GRAY87 = RGB(222, 222, 222)
    GRAY88 = RGB(224, 224, 224)
    GRAY89 = RGB(227, 227, 227)
    GRAY9 = RGB(23, 23, 23)
    GRAY90 = RGB(229, 229, 229)
    GRAY91 = RGB(232, 232, 232)
    GRAY92 = RGB(235, 235, 235)
    GRAY93 = RGB(237, 237, 237)
    GRAY94 = RGB(240, 240, 240)
    GRAY95 = RGB(242, 242, 242)
    GRAY97 = RGB(247, 247, 247)
    GRAY98 = RGB(250, 250, 250)
    GRAY99 = RGB(252, 252, 252)
    GREEN = RGB(0, 128, 0)
    GREEN1 = RGB(0, 255, 0)
    GREEN2 = RGB(0, 238, 0)
    GREEN3 = RGB(0, 205, 0)
    GREEN4 = RGB(0, 139, 0)
    GREENYELLOW = RGB(173, 255, 47)
    HONEYDEW1 = RGB(240, 255, 240)
    HONEYDEW2 = RGB(224, 238, 224)
    HONEYDEW3 = RGB(193, 205, 193)
    HONEYDEW4 = RGB(131, 139, 131)
    HOTPINK = RGB(255, 105, 180)
    HOTPINK1 = RGB(255, 110, 180)
    HOTPINK2 = RGB(238, 106, 167)
    HOTPINK3 = RGB(205, 96, 144)
    HOTPINK4 = RGB(139, 58, 98)
    INDIANRED = RGB(176, 23, 31)
    INDIANRED = RGB(205, 92, 92)
    INDIANRED1 = RGB(255, 106, 106)
    INDIANRED2 = RGB(238, 99, 99)
    INDIANRED3 = RGB(205, 85, 85)
    INDIANRED4 = RGB(139, 58, 58)
    INDIGO = RGB(75, 0, 130)
    IVORY1 = RGB(255, 255, 240)
    IVORY2 = RGB(238, 238, 224)
    IVORY3 = RGB(205, 205, 193)
    IVORY4 = RGB(139, 139, 131)
    IVORYBLACK = RGB(41, 36, 33)
    KHAKI = RGB(240, 230, 140)
    KHAKI1 = RGB(255, 246, 143)
    KHAKI2 = RGB(238, 230, 133)
    KHAKI3 = RGB(205, 198, 115)
    KHAKI4 = RGB(139, 134, 78)
    LAVENDER = RGB(230, 230, 250)
    LAVENDERBLUSH1 = RGB(255, 240, 245)
    LAVENDERBLUSH2 = RGB(238, 224, 229)
    LAVENDERBLUSH3 = RGB(205, 193, 197)
    LAVENDERBLUSH4 = RGB(139, 131, 134)
    LAWNGREEN = RGB(124, 252, 0)
    LEMONCHIFFON1 = RGB(255, 250, 205)
    LEMONCHIFFON2 = RGB(238, 233, 191)
    LEMONCHIFFON3 = RGB(205, 201, 165)
    LEMONCHIFFON4 = RGB(139, 137, 112)
    LIGHTBLUE = RGB(173, 216, 230)
    LIGHTBLUE1 = RGB(191, 239, 255)
    LIGHTBLUE2 = RGB(178, 223, 238)
    LIGHTBLUE3 = RGB(154, 192, 205)
    LIGHTBLUE4 = RGB(104, 131, 139)
    LIGHTCORAL = RGB(240, 128, 128)
    LIGHTCYAN1 = RGB(224, 255, 255)
    LIGHTCYAN2 = RGB(209, 238, 238)
    LIGHTCYAN3 = RGB(180, 205, 205)
    LIGHTCYAN4 = RGB(122, 139, 139)
    LIGHTGOLDENROD1 = RGB(255, 236, 139)
    LIGHTGOLDENROD2 = RGB(238, 220, 130)
    LIGHTGOLDENROD3 = RGB(205, 190, 112)
    LIGHTGOLDENROD4 = RGB(139, 129, 76)
    LIGHTGOLDENRODYELLOW = RGB(250, 250, 210)
    LIGHTGREY = RGB(211, 211, 211)
    LIGHTPINK = RGB(255, 182, 193)
    LIGHTPINK1 = RGB(255, 174, 185)
    LIGHTPINK2 = RGB(238, 162, 173)
    LIGHTPINK3 = RGB(205, 140, 149)
    LIGHTPINK4 = RGB(139, 95, 101)
    LIGHTSALMON1 = RGB(255, 160, 122)
    LIGHTSALMON2 = RGB(238, 149, 114)
    LIGHTSALMON3 = RGB(205, 129, 98)
    LIGHTSALMON4 = RGB(139, 87, 66)
    LIGHTSEAGREEN = RGB(32, 178, 170)
    LIGHTSKYBLUE = RGB(135, 206, 250)
    LIGHTSKYBLUE1 = RGB(176, 226, 255)
    LIGHTSKYBLUE2 = RGB(164, 211, 238)
    LIGHTSKYBLUE3 = RGB(141, 182, 205)
    LIGHTSKYBLUE4 = RGB(96, 123, 139)
    LIGHTSLATEBLUE = RGB(132, 112, 255)
    LIGHTSLATEGRAY = RGB(119, 136, 153)
    LIGHTSTEELBLUE = RGB(176, 196, 222)
    LIGHTSTEELBLUE1 = RGB(202, 225, 255)
    LIGHTSTEELBLUE2 = RGB(188, 210, 238)
    LIGHTSTEELBLUE3 = RGB(162, 181, 205)
    LIGHTSTEELBLUE4 = RGB(110, 123, 139)
    LIGHTYELLOW1 = RGB(255, 255, 224)
    LIGHTYELLOW2 = RGB(238, 238, 209)
    LIGHTYELLOW3 = RGB(205, 205, 180)
    LIGHTYELLOW4 = RGB(139, 139, 122)
    LIMEGREEN = RGB(50, 205, 50)
    LINEN = RGB(250, 240, 230)
    MAGENTA = RGB(255, 0, 255)
    MAGENTA2 = RGB(238, 0, 238)
    MAGENTA3 = RGB(205, 0, 205)
    MAGENTA4 = RGB(139, 0, 139)
    MANGANESEBLUE = RGB(3, 168, 158)
    MAROON = RGB(128, 0, 0)
    MAROON1 = RGB(255, 52, 179)
    MAROON2 = RGB(238, 48, 167)
    MAROON3 = RGB(205, 41, 144)
    MAROON4 = RGB(139, 28, 98)
    MEDIUMORCHID = RGB(186, 85, 211)
    MEDIUMORCHID1 = RGB(224, 102, 255)
    MEDIUMORCHID2 = RGB(209, 95, 238)
    MEDIUMORCHID3 = RGB(180, 82, 205)
    MEDIUMORCHID4 = RGB(122, 55, 139)
    MEDIUMPURPLE = RGB(147, 112, 219)
    MEDIUMPURPLE1 = RGB(171, 130, 255)
    MEDIUMPURPLE2 = RGB(159, 121, 238)
    MEDIUMPURPLE3 = RGB(137, 104, 205)
    MEDIUMPURPLE4 = RGB(93, 71, 139)
    MEDIUMSEAGREEN = RGB(60, 179, 113)
    MEDIUMSLATEBLUE = RGB(123, 104, 238)
    MEDIUMSPRINGGREEN = RGB(0, 250, 154)
    MEDIUMTURQUOISE = RGB(72, 209, 204)
    MEDIUMVIOLETRED = RGB(199, 21, 133)
    MELON = RGB(227, 168, 105)
    MIDNIGHTBLUE = RGB(25, 25, 112)
    MINT = RGB(189, 252, 201)
    MINTCREAM = RGB(245, 255, 250)
    MISTYROSE1 = RGB(255, 228, 225)
    MISTYROSE2 = RGB(238, 213, 210)
    MISTYROSE3 = RGB(205, 183, 181)
    MISTYROSE4 = RGB(139, 125, 123)
    MOCCASIN = RGB(255, 228, 181)
    NAVAJOWHITE1 = RGB(255, 222, 173)
    NAVAJOWHITE2 = RGB(238, 207, 161)
    NAVAJOWHITE3 = RGB(205, 179, 139)
    NAVAJOWHITE4 = RGB(139, 121, 94)
    NAVY = RGB(0, 0, 128)
    OLDLACE = RGB(253, 245, 230)
    OLIVE = RGB(128, 128, 0)
    OLIVEDRAB = RGB(107, 142, 35)
    OLIVEDRAB1 = RGB(192, 255, 62)
    OLIVEDRAB2 = RGB(179, 238, 58)
    OLIVEDRAB3 = RGB(154, 205, 50)
    OLIVEDRAB4 = RGB(105, 139, 34)
    ORANGE = RGB(255, 128, 0)
    ORANGE1 = RGB(255, 165, 0)
    ORANGE2 = RGB(238, 154, 0)
    ORANGE3 = RGB(205, 133, 0)
    ORANGE4 = RGB(139, 90, 0)
    ORANGERED1 = RGB(255, 69, 0)
    ORANGERED2 = RGB(238, 64, 0)
    ORANGERED3 = RGB(205, 55, 0)
    ORANGERED4 = RGB(139, 37, 0)
    ORCHID = RGB(218, 112, 214)
    ORCHID1 = RGB(255, 131, 250)
    ORCHID2 = RGB(238, 122, 233)
    ORCHID3 = RGB(205, 105, 201)
    ORCHID4 = RGB(139, 71, 137)
    PALEGOLDENROD = RGB(238, 232, 170)
    PALEGREEN = RGB(152, 251, 152)
    PALEGREEN1 = RGB(154, 255, 154)
    PALEGREEN2 = RGB(144, 238, 144)
    PALEGREEN3 = RGB(124, 205, 124)
    PALEGREEN4 = RGB(84, 139, 84)
    PALETURQUOISE1 = RGB(187, 255, 255)
    PALETURQUOISE2 = RGB(174, 238, 238)
    PALETURQUOISE3 = RGB(150, 205, 205)
    PALETURQUOISE4 = RGB(102, 139, 139)
    PALEVIOLETRED = RGB(219, 112, 147)
    PALEVIOLETRED1 = RGB(255, 130, 171)
    PALEVIOLETRED2 = RGB(238, 121, 159)
    PALEVIOLETRED3 = RGB(205, 104, 137)
    PALEVIOLETRED4 = RGB(139, 71, 93)
    PAPAYAWHIP = RGB(255, 239, 213)
    PEACHPUFF1 = RGB(255, 218, 185)
    PEACHPUFF2 = RGB(238, 203, 173)
    PEACHPUFF3 = RGB(205, 175, 149)
    PEACHPUFF4 = RGB(139, 119, 101)
    PEACOCK = RGB(51, 161, 201)
    PINK = RGB(255, 192, 203)
    PINK1 = RGB(255, 181, 197)
    PINK2 = RGB(238, 169, 184)
    PINK3 = RGB(205, 145, 158)
    PINK4 = RGB(139, 99, 108)
    PLUM = RGB(221, 160, 221)
    PLUM1 = RGB(255, 187, 255)
    PLUM2 = RGB(238, 174, 238)
    PLUM3 = RGB(205, 150, 205)
    PLUM4 = RGB(139, 102, 139)
    POWDERBLUE = RGB(176, 224, 230)
    PURPLE = RGB(128, 0, 128)
    PURPLE1 = RGB(155, 48, 255)
    PURPLE2 = RGB(145, 44, 238)
    PURPLE3 = RGB(125, 38, 205)
    PURPLE4 = RGB(85, 26, 139)
    RASPBERRY = RGB(135, 38, 87)
    RAWSIENNA = RGB(199, 97, 20)
    RED1 = RGB(255, 0, 0)
    RED2 = RGB(238, 0, 0)
    RED3 = RGB(205, 0, 0)
    RED4 = RGB(139, 0, 0)
    ROSYBROWN = RGB(188, 143, 143)
    ROSYBROWN1 = RGB(255, 193, 193)
    ROSYBROWN2 = RGB(238, 180, 180)
    ROSYBROWN3 = RGB(205, 155, 155)
    ROSYBROWN4 = RGB(139, 105, 105)
    ROYALBLUE = RGB(65, 105, 225)
    ROYALBLUE1 = RGB(72, 118, 255)
    ROYALBLUE2 = RGB(67, 110, 238)
    ROYALBLUE3 = RGB(58, 95, 205)
    ROYALBLUE4 = RGB(39, 64, 139)
    SALMON = RGB(250, 128, 114)
    SALMON1 = RGB(255, 140, 105)
    SALMON2 = RGB(238, 130, 98)
    SALMON3 = RGB(205, 112, 84)
    SALMON4 = RGB(139, 76, 57)
    SANDYBROWN = RGB(244, 164, 96)
    SAPGREEN = RGB(48, 128, 20)
    SEAGREEN1 = RGB(84, 255, 159)
    SEAGREEN2 = RGB(78, 238, 148)
    SEAGREEN3 = RGB(67, 205, 128)
    SEAGREEN4 = RGB(46, 139, 87)
    SEASHELL1 = RGB(255, 245, 238)
    SEASHELL2 = RGB(238, 229, 222)
    SEASHELL3 = RGB(205, 197, 191)
    SEASHELL4 = RGB(139, 134, 130)
    SEPIA = RGB(94, 38, 18)
    SGIBEET = RGB(142, 56, 142)
    SGIBRIGHTGRAY = RGB(197, 193, 170)
    SGICHARTREUSE = RGB(113, 198, 113)
    SGIDARKGRAY = RGB(85, 85, 85)
    SGIGRAY12 = RGB(30, 30, 30)
    SGIGRAY16 = RGB(40, 40, 40)
    SGIGRAY32 = RGB(81, 81, 81)
    SGIGRAY36 = RGB(91, 91, 91)
    SGIGRAY52 = RGB(132, 132, 132)
    SGIGRAY56 = RGB(142, 142, 142)
    SGIGRAY72 = RGB(183, 183, 183)
    SGIGRAY76 = RGB(193, 193, 193)
    SGIGRAY92 = RGB(234, 234, 234)
    SGIGRAY96 = RGB(244, 244, 244)
    SGILIGHTBLUE = RGB(125, 158, 192)
    SGILIGHTGRAY = RGB(170, 170, 170)
    SGIOLIVEDRAB = RGB(142, 142, 56)
    SGISALMON = RGB(198, 113, 113)
    SGISLATEBLUE = RGB(113, 113, 198)
    SGITEAL = RGB(56, 142, 142)
    SIENNA = RGB(160, 82, 45)
    SIENNA1 = RGB(255, 130, 71)
    SIENNA2 = RGB(238, 121, 66)
    SIENNA3 = RGB(205, 104, 57)
    SIENNA4 = RGB(139, 71, 38)
    SILVER = RGB(192, 192, 192)
    SKYBLUE = RGB(135, 206, 235)
    SKYBLUE1 = RGB(135, 206, 255)
    SKYBLUE2 = RGB(126, 192, 238)
    SKYBLUE3 = RGB(108, 166, 205)
    SKYBLUE4 = RGB(74, 112, 139)
    SLATEBLUE = RGB(106, 90, 205)
    SLATEBLUE1 = RGB(131, 111, 255)
    SLATEBLUE2 = RGB(122, 103, 238)
    SLATEBLUE3 = RGB(105, 89, 205)
    SLATEBLUE4 = RGB(71, 60, 139)
    SLATEGRAY = RGB(112, 128, 144)
    SLATEGRAY1 = RGB(198, 226, 255)
    SLATEGRAY2 = RGB(185, 211, 238)
    SLATEGRAY3 = RGB(159, 182, 205)
    SLATEGRAY4 = RGB(108, 123, 139)
    SNOW1 = RGB(255, 250, 250)
    SNOW2 = RGB(238, 233, 233)
    SNOW3 = RGB(205, 201, 201)
    SNOW4 = RGB(139, 137, 137)
    SPRINGGREEN = RGB(0, 255, 127)
    SPRINGGREEN1 = RGB(0, 238, 118)
    SPRINGGREEN2 = RGB(0, 205, 102)
    SPRINGGREEN3 = RGB(0, 139, 69)
    STEELBLUE = RGB(70, 130, 180)
    STEELBLUE1 = RGB(99, 184, 255)
    STEELBLUE2 = RGB(92, 172, 238)
    STEELBLUE3 = RGB(79, 148, 205)
    STEELBLUE4 = RGB(54, 100, 139)
    TAN = RGB(210, 180, 140)
    TAN1 = RGB(255, 165, 79)
    TAN2 = RGB(238, 154, 73)
    TAN3 = RGB(205, 133, 63)
    TAN4 = RGB(139, 90, 43)
    TEAL = RGB(0, 128, 128)
    THISTLE = RGB(216, 191, 216)
    THISTLE1 = RGB(255, 225, 255)
    THISTLE2 = RGB(238, 210, 238)
    THISTLE3 = RGB(205, 181, 205)
    THISTLE4 = RGB(139, 123, 139)
    TOMATO1 = RGB(255, 99, 71)
    TOMATO2 = RGB(238, 92, 66)
    TOMATO3 = RGB(205, 79, 57)
    TOMATO4 = RGB(139, 54, 38)
    TURQUOISE = RGB(64, 224, 208)
    TURQUOISE1 = RGB(0, 245, 255)
    TURQUOISE2 = RGB(0, 229, 238)
    TURQUOISE3 = RGB(0, 197, 205)
    TURQUOISE4 = RGB(0, 134, 139)
    TURQUOISEBLUE = RGB(0, 199, 140)
    VIOLET = RGB(238, 130, 238)
    VIOLETRED = RGB(208, 32, 144)
    VIOLETRED1 = RGB(255, 62, 150)
    VIOLETRED2 = RGB(238, 58, 140)
    VIOLETRED3 = RGB(205, 50, 120)
    VIOLETRED4 = RGB(139, 34, 82)
    WARMGREY = RGB(128, 128, 105)
    WHEAT = RGB(245, 222, 179)
    WHEAT1 = RGB(255, 231, 186)
    WHEAT2 = RGB(238, 216, 174)
    WHEAT3 = RGB(205, 186, 150)
    WHEAT4 = RGB(139, 126, 102)
    WHITE = RGB(255, 255, 255)
    WHITESMOKE = RGB(245, 245, 245)
    YELLOW1 = RGB(255, 255, 0)
    YELLOW2 = RGB(238, 238, 0)
    YELLOW3 = RGB(205, 205, 0)
    YELLOW4 = RGB(139, 139, 0)