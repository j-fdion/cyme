"""
Décorateurs génériques pour les behavior tree. Il y a toujours un seul child.
-----------------------------------------------------------------------------
"""

from .nodetypes import Task, Decorator


class Delay(Decorator):
    """Decorator pour un simple delay qui peut-être fractionaire."""

    def __init__(self, delay=0):
        """Crée une instance du decorateur.

        :param float delay: durée du délai en secondes (défaut 0).
        """
        super().__init__()
        self._delay = -1
        self.delay = -1
        self.set_delay(delay)

    def set_delay(self, delay):
        self._delay = delay
        self.delay = delay

    def run(self):
        """Tick le décorateur pour une unité.

        :return: ``Task.RUNNING`` tant que delay non atteint, sinon le \
        status du child et on reset le delay si celui-ci est autre que ``Task.RUNNING``
        """
        # print("compteur: ", self.delay)
        if self.delay > 1:
            self.delay -= 1
            return Task.RUNNING
        else:
            status = self._children[0].run()
            if status == Task.SUCCES:
                self.delay += self._delay - 1
                return Task.SUCCES
            elif status == Task.RUNNING:
                return Task.RUNNING
            else:
                self.delay += self._delay - 1
                return Task.ECHEC

    def add_child(self, c):
        """Ajoute un child au noeud."""
        super().add_child(c)


class Inverter(Decorator):
    """ Retourne l'état contraire à son enfant"""

    def __init__(self):
        super().__init__()

    def run(self):
        """Tick le décorateur pour une unité.

        :return: ``Task.RUNNING`` si le status du child est ``Task.RUNNING`` \
        sinon il transmet l'état contraire
        """
        status = self._children[0].run()
        if status == Task.SUCCES:
            return Task.ECHEC
        else:
            return Task.SUCCES

    def add_child(self, c):
        """Ajoute un child au noeud."""
        super().add_child(c)


class Succes(Decorator):
    """ Retourne l'état SUCCES peu importe l'état de son enfant"""

    def __init__(self):
        super().__init__()

    def run(self):
        """Tick le décorateur pour une unité.

        :return: ``Task.SUCCES``
        """
        status = self._children[0].run()
        return Task.SUCCES

    def add_child(self, c):
        """Ajoute un child au noeud."""
        super().add_child(c)


class Echec(Decorator):
    """ Retourne l'état ECHEC peu importe l'état de son enfant"""

    def __init__(self):
        super().__init__()

    def run(self):
        """Tick le décorateur pour une unité.

        :return: ``Task.ECHEC``
        """
        status = self._children[0].run()
        return Task.ECHEC

    def add_child(self, c):
        """Ajoute un child au noeud."""
        super().add_child(c)


class RepeatUntilSucces(Decorator):
    """ Retourne l'état RUNNING tant que son enfant n'a pas retourné SUCCES"""

    def __init__(self):
        super().__init__()

    def run(self):
        """Tick le décorateur pour une unité.

        :return: ``Task.RUNNING`` tant que status du child n'est pas ``Task.SUCCES`` \
        sinon il transmet le ``Task.SUCCES``
        """
        status = self._children[0].run()
        if status == Task.SUCCES:
            return Task.SUCCES
        else:
            return Task.RUNNING

    def add_child(self, c):
        """Ajoute un child au noeud."""
        super().add_child(c)


class RepeatUntilEchec(Decorator):
    """ Retourne l'état RUNNING tant que son enfant n'a pas retourné ECHEC"""

    def __init__(self):
        super().__init__()

    def run(self):
        """Tick le décorateur pour une unité.

        :return: ``Task.RUNNING`` tant que status du child n'est pas ``Task.ECHEC`` \
        sinon il transmet le ``Task.ECHEC``
        """
        status = self._children[0].run()
        if status == Task.ECHEC:
            return Task.ECHEC
        else:
            return Task.RUNNING

    def add_child(self, c):
        """Ajoute un child au noeud."""
        super().add_child(c)


class Actif(Decorator):
    """Propage le tick au children seulement si target.actif est True ou pour continuer
    l'état ``Task.RUNNING`` du child. Ceci permet de forcer la nature atomique des opérations.
    """

    def __init__(self, target):
        """Crée une instance du décorateur.

        :param target: lien sur un objet ayant un attribut ``actif``.
        """
        super().__init__()
        self.target = target  # doit avoir la var actif
        self.prev_status = Task.SUCCES  # initialisation (pas en R)

    def run(self):
        """Tick le décorateur pour une unité.

        :return: status du child s'il est running ou que target.actif est True, sinon ``Task.ECHEC``.
        """
        status = Task.ECHEC
        if self.prev_status == Task.RUNNING:
            status = self._children[0].run()
        elif self.target.actif:
            status = self._children[0].run()
        self.prev_status = status
        return status

    def add_child(self, c):
        """Ajoute un child au noeud."""
        super().add_child(c)
