"""
Algorithme de recherche d'un chemin dans un graphe.
---------------------------------------------------
"""
import heapq

class aStar:
    @staticmethod
    def trouverChemin(start, goal, masque = 0xFFFFFFFF):
        if start in goal.voisins:
            return [goal]
        else:
            return aStar.construireChemin(start, goal, masque)

    @staticmethod
    def construireChemin(start, goal, masque = 0xFFFFFFFF):
        """ Algorithme pour trouver le chemin le plus cours entre 2 noeuds du graphe.
        Références:

            * http://en.wikipedia.org/wiki/A*_search_algorithm
            * http://www.redblobgames.com/pathfinding/a-star/introduction.html
            * http://www.redblobgames.com/pathfinding/a-star/implementation.html
        """
        openSet=set()
        closeSet=set()
        openHeap=[]

        came_from={}
        g_score={}
        f_score={}

        came_from[start]=None
        f_score[start]=0
        g_score[start]=0

        openSet.add(start)
        t=(0, start)
        heapq.heappush(openHeap, t)
        while openSet:
            current=heapq.heappop(openHeap)[1]
            if current==goal:
                return aStar.construireCheminHelper(start, goal, came_from)
            openSet.remove(current)
            closeSet.add(current)
            voisins=current.voisins
            for n in voisins:
                if n.coloris & masque > 0:
                    if n not in closeSet:
                        g_score[n]=g_score[current]+aStar.dist(current, n)
                        f_score[n]=g_score[n]+aStar.heuristic(goal, n)
                        if n not in openSet:
                            openSet.add(n)
                            t=(f_score[n], n)
                            heapq.heappush(openHeap, t)
                        came_from[n]=current
        return []

    @staticmethod
    def construireCheminHelper(start, goal, came_from):
        #On construit une liste à partir du dictionnaire en partant de goal vers start.
        current=goal
        chemin=[current]
        while current is not start:
            current=came_from[current]
            chemin.append(current)
        #chemin.reverse()
        return chemin

    @staticmethod
    def dist(node, goal):
        #distance eucledienne au carre
        dx=node.box.pos[0]-goal.box.pos[0]
        dy=node.box.pos[1]-goal.box.pos[1]
        return dx*dx+dy*dy

    @staticmethod
    def heuristic(node, goal):
        #heuristic il est plus couteux de se promener dans les allées des secteurs
        #que dans les passages
        #if goal.nature == Noeud.INTR:
        return aStar.dist(node, goal)
        #elif goal.nature == Noeud.CUVE:
        #return 2*dist(node, goal)
        #elif goal.nature == Noeud.PASS:
        #return dist(node, goal)
