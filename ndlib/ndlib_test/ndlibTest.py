import unittest
import networkx as nx
import sys
sys.path.append("..")
import ndlib.VoterModel as vm
import ndlib.SznajdModel as sm
import ndlib.MajorityRuleModel as mrm
import ndlib.KerteszThresholdModel as ktm
import numpy as np

__author__ = 'rossetti'
__license__ = "GPL"
__email__ = "giulio.rossetti@gmail.com"


class NdlibTest(unittest.TestCase):

    # def test_voter_model(self):
    #     g = nx.erdos_renyi_graph(1000, 0.1)
    #     model = vm.VoterModel(g)
    #     model.set_initial_status({'model': {'percentage_infected': 0.2}})
    #     iterations = model.iteration_bunch(10)
    #     self.assertEqual(len(iterations), 10)
    #
    # def test_sznajd_model(self):
    #     g = nx.erdos_renyi_graph(1000, 0.1)
    #     model = sm.SznajdModel(g)
    #     model.set_initial_status({'model': {'percentage_infected': 0.2}})
    #     iterations = model.iteration_bunch(10)
    #     self.assertEqual(len(iterations), 10)
    #
    # def test_majorityrule_model(self):
    #     g = nx.complete_graph(100)
    #     model = mrm.MajorityRuleModel(g, {'q': 3})
    #     model.set_initial_status({'model': {'percentage_infected': 0.6}})
    #     iterations = model.iteration_bunch(10)
    #     self.assertEqual(len(iterations), 10)

    def test_janos_model(self):
        g = nx.erdos_renyi_graph(100, 0.1)
        model = ktm.JanosThresholdModel(g, {'adopter_rate': 0.4, 'blocked': 10})
        #avg_degree = np.mean(g.graph.degree(g.graph.nodes()).values())
        threshold = 0.2
        # if 0 < threshold <= 1/avg_degree:
        threshold_list = (threshold,)
        for i in range(0, g.number_of_nodes()-1):
            threshold_list = threshold_list + (threshold,)
        model.set_initial_status({'model': {'percentage_infected': 0.0}, 'nodes': {'threshold': threshold_list}})
        iterations = model.iteration_bunch(100)
        self.assertEqual(len(iterations), 100)
        # else:

