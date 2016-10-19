from DiffusionModel import DiffusionModel
import networkx as nx
import numpy as np
from scipy import stats

__author__ = "Letizia Milli"
__email__ = "letizia.milli@di.unipi.it"

class JanosThresholdModel(DiffusionModel):
    # avg_degree = 0

    def iteration(self):
        """

        """

        actual_status = {node: nstatus for node, nstatus in self.status.iteritems()}

        if self.actual_iteration == 0:
            # self.avg_degree = np.mean(self.graph.degree(self.graph.nodes()).values())
            number_node_blocked = int(float(self.graph.number_of_nodes()) * float(self.params['blocked']) / 100.0)
            for i in range(0, number_node_blocked + 1):
                # select a random node
                node = self.graph.nodes()[np.random.randint(0, self.graph.number_of_nodes())]
                while self.status[node] == -1:
                    node = self.graph.nodes()[np.random.randint(0, self.graph.number_of_nodes())]
                # node blocked
                self.status[node] = -1
            self.actual_iteration += 1
            return 0, actual_status

        # select a random susceptible node
        node = self.graph.nodes()[np.random.randint(0, self.graph.number_of_nodes())]
        while self.status[node] == -1:
            node = self.graph.nodes()[np.random.randint(0, self.graph.number_of_nodes())]

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
                if infected_ratio >= self.params['nodes']['threshold'][node]:
                    actual_status[node] = 1

        delta = self.status_delta(actual_status)
        self.status = actual_status
        self.actual_iteration += 1

        # return self.actual_iteration, actual_status
        return self.actual_iteration, delta
