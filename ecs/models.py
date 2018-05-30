"""
Entity, Component, and System classes.
--------------------------------------
"""
from abc import ABCMeta, abstractmethod

class Entity(object):
    """Encapsulation of a GUID to use in the entity database."""

    def __init__(self, guid, name=""):
        """:param guid: globally unique identifier
        :type guid: :class:`int`
        """
        self._name = name
        self._guid = guid

    def __repr__(self):
        return '{0}({1})'.format(type(self).__name__, self._guid)

    def __hash__(self):
        return self._guid

    def __eq__(self, other):
        return self._guid == hash(other)

    def name(self):
        return self._name

class Component(object):
        pass

class System(metaclass=ABCMeta):
    """An object that represents an operation on a set of objects from the game
    database. The :meth:`update` method must be implemented.
    """

    def __init__(self):
        self.entity_manager = None
        """This system's entity manager. It is set for each system when it is
        added to a system manager, so a system may not (reasonably) use
        multiple entity managers. The reason is performance. See
        :meth:`ecs.managers.SystemManager.update()` for more information.
        """
        self.system_manager = None
        """The system manager to which this system belongs. Again, a system is
        only allowed to belong to one at a time."""

    @abstractmethod
    def init(self):
        print("System's init() method was called.")

    @abstractmethod
    def reset(self):
        print("System's reset() method was called.")

    @abstractmethod
    def update(self, dt):
        """Run the system for this frame. This method is called by the system
        manager, and is where the functionality of the system is implemented.

        :param entity_manager: this system's entity manager, used for
            querying components
        :type entity_manager: :class:`ecs.managers.EntityManager`
        :param dt: delta time, or elapsed time for this frame
        :type dt: :class:`float`
        """
        print("System's update() method was called: dt={}".format(dt))


class UpdateLogic(System):
    """ Le système générique de mise-à-jour (update) de la logique. """

    def __init__(self, components):
        """
        :param components: liste de ``ecs.models.Component`` pour lesquels on doit faire 
            une mise-à-jour à chaque unité de temps, via la méthode ``update`` des instances
        """
        super().__init__()
        self.components = components

    def init(self):
        pass

    def reset(self):
        pass

    def update(self, dt):
        """ Boucle sur les ``ecs.models.Component``, pour appeler ``update`` sur 
        les instances de components de chacune des sortes. """
        for component in self.components:
            for entity, c in self.entity_manager.pairs_for_type(component):
                c.update()


