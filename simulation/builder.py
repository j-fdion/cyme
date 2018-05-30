"""
Builder pour construire le structure de base du modèle.
-------------------------------------------------------
"""
from .. import ecs
from . import graphe
from . import base


class Builder(object):
    """ Builder de la structure de base d'un modele pour la simulation. """

    def __init__(self, bd, entity_manager):
        """Crée une instance du ``Builder``.

        :param bd: bd avec les directives de construction (typiquement, contenu dans le fichier csv ``plan.csv``)
        :type bd: :class:`sim.base.base.TripleManager`
        :param entity_manager: entity manager pour créer et gérer les ``Entity``
        :type entity_manager: :class:`ecs.managers.EntityManager`
        """
        self.entite = {}
        self.bd = bd
        self.entity_manager = entity_manager
        self.factoryNom = ["box"]
        self.factoryFct = [self.rebuildBox]
        m = self.bd.getv(("modele", "nom"))
        if m is not None:
            ######## le look (background) ########
            nblook = int(self.bd.getv((m, "nblook")))
            for i in range(nblook):  # on load les background
                look = self.bd.getv((m, "look" + str(i)))
                if look is not None:
                    # position et size du modele lui-meme
                    posref = self.bd.getv(("modele", "posref"))
                    pos = (posref[0] + look[0], posref[1] + look[1])
                    size = (look[2], look[3])
                    b = graphe.Box(pos, size)
                    b.sorte = 0
                    a = self.entity_manager.create_entity()
                    self.entity_manager.add_component(a, b)
            self.rebuildModele(m)
        l = self.bd.getv(("lienglobal", "nombre"))
        # on suppose que les graphes necessaires existent
        if l is not None: self.rebuildLiens(l)

    def rebuildLiens(self, nbl):
        """On boucle sur les liens (arêtes entre des noeuds du graphe), qu'il faut 
        créer via ``rebuildUnLien``. Par exemple, pour le lien no 0, la clé du lien 
        à recréer est de la forme ("lienglobal0",0).

        :param nbl: nombre de liens à reconstruire selon les directives de la bd.
        """
        # print("  Reconstruction de", nbl, "liens global via des composants aretes")
        nbliens = int(nbl)
        ls = []
        for i in range(nbliens):  # on load les noms de toutes les structures
            y = self.bd.getv(("lienglobal" + str(i), str(i)))
            if (y is not None): ls.append(y)
        for i, lien in enumerate(ls):
            # print("  Lien global:",i,lien)
            self.rebuildUnLien(i, lien)

    def rebuildUnLien(self, i, lien):
        """Ajouter un lien global avec une nouvelle arête: (lienglobal i,A-B,C-D) ou (A,B,obj1), (C,D,obj2) 
        sont dans la bd. On *crée* une ``Entity`` avec les composants ``Arete`` (obj1,obj2) et ``Ligne``, 
        ensuite on update ``ina``, ``oua`` dans les ``Noeud`` obj1 et obj2. Finalement, on ajoute un
        triplet dans la bd: (A-B,C-D,a), afin d'y référer facilement via un handle.

        :param int i: ième lien global
        :param str lien: origine du lien à reconstruire, le target est dans la bd \
        comme valeur de la clef ("lienglobal i",lien), i.e. lien -> bd.getv(("lienglobal i",lien))
        """
        # print("  Reconstruction du lien", lien)
        x = self.bd.getv(("lienglobal" + str(i), lien))
        if x is not None:
            # print("  **** Le lien global de", lien, "a", x)
            nn = self.bd.getv(tuple(i for i in lien.split('-')))
            n = self.bd.getv(tuple(i for i in x.split('-')))
            a = self.entity_manager.create_entity()  # on cree une entity a
            r = graphe.Arete(a, nn, n)  # on cree un composant arete lie a l'entite a
            self.entity_manager.add_component(a, r)
            nn.oua.append(r)
            n.ina.append(r)
            b1 = self.entity_manager.component_for_entity(nn.entity, graphe.Box)
            b2 = self.entity_manager.component_for_entity(n.entity, graphe.Box)
            l = graphe.Ligne(list(b1.cent) + list(b2.cent))
            self.entity_manager.add_component(a, l)
            self.bd.add(lien, x, r, "Lien arete entre" + lien + x)

    def rebuildModele(self, modele):
        """Reconstruction du modèle en identifiant le nombre de structure dans la BD
        et en les reconstruisant via ``rebuildStructure``.

        :param str modele: nom du modèle (récupéré de la BD).
        """
        # print("  Reconstruction du modele", modele)
        x = self.bd.getv((modele, "nbstruct"))
        if x is not None:
            self.nbstruct = int(x)
        else:
            self.nbstruct = 0
        # print("  Le modele", modele, "a", self.nbstruct, "structures")
        ms = []
        for i in range(self.nbstruct):  # on load les noms de toutes les structures
            y = self.bd.getv((modele, "struct" + str(i)))
            if (y is not None): ms.append(y)
        # print("  Structures du modeles", modele, ":")
        for m in ms:
            self.rebuildStructure(m)

    def rebuildStructure(self, structure):
        """Reconstruction d'une structure du modèle via la BD. C'est généralement
        un ensemble de composants ``Box`` à refaire via ``rebuildBox``."""
        # print("    - Rebuild structure", structure)
        for i in range(len(self.factoryNom)):
            if self.bd.getv((structure, self.factoryNom[i])) is not None:
                self.factoryFct[i](structure)

    def rebuildBox(self, structure):
        """Reconstruction des composants ``Box`` d'une structure du modèle:

        1. on cherche d'abord le nb de box à faire avec la clé (structure, "box")
        2. on cherche la box principale à faire avec la clé (structure, "bbox")
        3. s'il y a un item avec la clé (structure, "dbox"), c'est un couple \
        pour la translation lors de la création des autres ``Box``
        4. sinon, s'il y a un item avec la clé (structure, "cbox"), c'est un tuple \
        pour la translation circulaire lors de la création des autres ``Box``

        :param str structure: nom de la structure qu'on recrée via des ``Box``.
        """
        # nbox: nb de box a faire (si >1, il faut un dbox)
        x = self.bd.getv((structure, "box"))
        if (x is not None):
            nbox = int(x)
        else:
            nbox = 0
        # si cas degenere sans box a faire, on termine
        if nbox == 0: return
        posref = self.bd.getv(("modele", "posref"))
        eb = []  # les entites crees avec un composant box
        # construction de la box principale
        # print("        -- Rebuild", nbox, "box")
        bbox = self.bd.getv((structure, "bbox"))
        if (bbox is None):
            print("        -- Erreur! Rebuild box: pas de bbox")
        else:
            # position et size
            pos = (posref[0] + bbox[0], posref[1] + bbox[1])
            size = (bbox[2], bbox[3])
            b = graphe.Box(pos, size)
            a = self.entity_manager.create_entity()
            self.entity_manager.add_component(a, b)
            eb.append(a)  # on conserve
        # construction des box complementaires
        if nbox > 1:
            dpos = self.bd.getv((structure, "dbox"))
            if (dpos is not None):  # on replique la box lineairement
                # dpos est un couple de translation de la position
                # print("dpos:", dpos)
                while (nbox > 1):
                    pos = (pos[0] + dpos[0], pos[1] + dpos[1])  # position
                    nbox -= 1
                    b = graphe.Box(pos, size)
                    a = self.entity_manager.create_entity()
                    self.entity_manager.add_component(a, b)
                    eb.append(a)  # on conserve
            else:
                cbox = self.bd.getv((structure, "cbox"))
                if (cbox is not None):  # on replique la box en circulaire
                    # print("cbox:", cbox)
                    fact = 1 + nbox / 4;
                    k = 0;
                    i = 1
                    while (nbox > 1):
                        while (nbox > 1 and i <= fact):
                            z = cbox[k]
                            i += 1
                            if (k % 2 == 0):
                                pos = (pos[0] + z, pos[1])
                            else:
                                pos = (pos[0], pos[1] + z)
                            # print(pos)
                            nbox -= 1
                            b = graphe.Box(pos, size)
                            a = self.entity_manager.create_entity()
                            self.entity_manager.add_component(a, b)
                            eb.append(a)  # on conserve
                        k += 1;
                        i = 1
        # on fait un graphe avec cette structure, si desire
        x = self.bd.getv((structure, "graphe"))
        if (x in ['true', 'True']):
            # print("Creation et ajout des composants Noeud et Arete")
            col = self.bd.getv((structure, "coloris"))
            n = None
            for i in range(len(eb)):  # on balai les entites avec un box
                e = eb[i]
                nn = n
                n = graphe.Noeud(e)
                if col is not None:
                    # couleur de coloriage du noeud selon sous-graphe
                    n.coloris = int(col, 16)
                if (i > 0):  # ajout arete entre des noeuds
                    a = self.entity_manager.create_entity()
                    r = graphe.Arete(a, nn, n)  # a est l'entite
                    self.entity_manager.add_component(a, r)
                    nn.oua.append(r)
                    n.ina.append(r)
                    b1 = self.entity_manager.component_for_entity(nn.entity, graphe.Box)
                    b2 = self.entity_manager.component_for_entity(n.entity, graphe.Box)
                    l = graphe.Ligne(list(b1.cent) + list(b2.cent))
                    self.entity_manager.add_component(a, l)
                else:
                    self.bd.add(structure, "debut", n, "Handle sur le Noeud du debut")
                self.entity_manager.add_component(e, n)
                b1 = self.entity_manager.component_for_entity(n.entity, graphe.Box)
                n.box = b1  # on place un handle dans sur le box dans le noeud
            self.bd.add(structure, "fin", n, "Handle sur le Noeud de fin")
        # nbhandle: nb de box a faire (si >1, il faut un dbox)
        x = self.bd.getv((structure, "nbhandle"))
        if x is not None:
            nbhandle = int(x)
        else:
            nbhandle = 0
        i = 0
        while nbhandle > 0:  # on a des liens a construire
            x = self.bd.getv((structure, "handle" + str(i)))
            nbhandle -= 1
            i += 1
            if x is not None:
                y = self.bd.getv((structure, x))
                if y is not None:
                    n = int(y)
                else:
                    n = 0
                if n > 0:
                    # print("Handle structure", structure, "debut +", n)
                    nn = self.bd.getv((structure, "debut"))
                    if nn is not None:
                        for j in range(n):
                            nn = nn.oua[0].to
                    self.bd.add(structure, x, nn)
                elif n < 0:
                    # print("Handle structure", structure, "fin", n)
                    nn = self.bd.getv((structure, "fin"))
                    if nn is not None:
                        for j in range(n*-1):
                            nn = nn.ina[0].fr
                    self.bd.add(structure, x, nn)
                    # print("Fin rebuild",structure,"\n")
