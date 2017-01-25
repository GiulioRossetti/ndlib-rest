from DiffusionModel import DiffusionModel
import networkx as nx
import numpy as np
from scipy import stats

__author__ = "Letizia Milli"
__email__ = "letizia.milli@di.unipi.it"


class JanosThresholdModel(DiffusionModel):

    def iteration(self):
        """

        """
        self.clean_initial_status([0, 1, -1])
        actual_status = {node: nstatus for node, nstatus in self.status.iteritems()}

        if self.actual_iteration == 0:
            if min(actual_status.values()) == 0:
                number_node_blocked = int(float(self.graph.number_of_nodes()) * float(self.params['blocked']))

                i = 0
                while i < number_node_blocked:
                    # select a random node
                    node = self.graph.nodes()[np.random.randint(0, self.graph.number_of_nodes())]

                    # node not infected
                    if actual_status[node] == 0:

                        # node blocked
                        actual_status[node] = -1
                        self.status[node] = -1
                        i += 1

            self.actual_iteration += 1
            return 0, actual_status

        for node in self.graph.nodes():
            if self.status[node] != -1:
                xk = (0, 1)
                pk = (1-self.params['adopter_rate'], self.params['adopter_rate'])
                probability = stats.rv_discrete(name='probability', values=(xk, pk))
                number_probability = probability.rvs()

                if number_probability == 1:
                    actual_status[node] = 1
                else:
                    neighbors = self.graph.neighbors(node)
                    if isinstance(self.graph, nx.DiGraph):
                        neighbors = self.graph.predecessors(node)

                    infected = 0
                    for v in neighbors:
                        infected += self.status[v]

                    if len(neighbors) > 0:
                        infected_ratio = float(infected)/len(neighbors)
                        if infected_ratio >= self.params['nodes']['threshold'][str(node)]:
                            actual_status[node] = 1

        delta = self.status_delta(actual_status)
        self.status = actual_status
        self.actual_iteration += 1

        return self.actual_iteration-1, delta
