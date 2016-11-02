import unittest
from requests import put, get, delete, post
import networkx as nx
from networkx.readwrite import json_graph
import json
import numpy as np

__author__ = 'rossetti'
__license__ = "GPL"
__email__ = "giulio.rossetti@gmail.com"

base = "http://127.0.0.1:5000"


class RESTTest(unittest.TestCase):

    def test_experiment_create_and_destroy(self):
        res = get('%s/api/Experiment' % base).json()
        token1 = res['token']
        self.assertIsNotNone(token1)

        res = delete('%s/api/Experiment' % base, data={'token': token1})
        self.assertEqual(res.status_code, 200)

        print "Experiment Create and Destroy: OK"

    def test_generate_er_graphs(self):
        res = get('%s/api/Experiment' % base).json()
        token2 = res['token']
        self.assertIsNotNone(token2)

        res = get('%s/api/Generators' % base).json()
        endpoints = res['endpoints']

        for e in endpoints:
            if e['name'] == 'ERGraph':
                gr = put("%s%s" % (base, e['uri']), data={'n': 400, 'p': 0.05, 'directed': True, 'token': token2})
                self.assertEqual(gr.status_code, 200)

        res = delete('%s/api/Experiment' % base, data={'token': token2})
        self.assertEqual(res.status_code, 200)

        print "Generate ERGraph: OK"

    def test_generate_ws_graphs(self):
        res = get('%s/api/Experiment' % base).json()
        token2 = res['token']
        self.assertIsNotNone(token2)

        res = get('%s/api/Generators' % base).json()
        endpoints = res['endpoints']

        for e in endpoints:
            if e['name'] == 'WSGraph':
                gr = put("%s%s" % (base, e['uri']), data={'n': 400, 'k': 3, 'p': 0.05, 'token': token2})
                self.assertEqual(gr.status_code, 200)

        res = delete('%s/api/Experiment' % base, data={'token': token2})
        self.assertEqual(res.status_code, 200)

        print "Generate WSSGraph: OK"

    def test_generate_ba_graphs(self):
        res = get('%s/api/Experiment' % base).json()
        token3 = res['token']
        self.assertIsNotNone(token3)

        res = get('%s/api/Generators' % base).json()
        endpoints = res['endpoints']

        for e in endpoints:
            if e['name'] == 'BAGraph':
                gr = put("%s%s" % (base, e['uri']), data={'n': 400, 'm': 3, 'token': token3})
                self.assertEqual(gr.status_code, 200)

        res = delete('%s/api/Experiment' % base, data={'token': token3})
        self.assertEqual(res.status_code, 200)

        print "Generate BAGraph: OK"

    def test_generate_load_real_network(self):
        res = get('%s/api/Experiment' % base).json()
        token4 = res['token']
        self.assertIsNotNone(token4)

        res = get('%s/api/Networks' % base).json()
        self.assertIn('networks', res)

        res = put('%s/api/Networks' % base, data={'name': 'Lastfm', 'token': token4})
        self.assertEqual(res.status_code, 200)
        print "Load Real Graph: OK"

        res = post('%s/api/GetGraph' % base, data={'token': token4}).json()
        self.assertNotIn('Status', res)
        print "Get Graph (available): OK"

        res = delete('%s/api/Networks' % base, data={'token': token4})
        self.assertEqual(res.status_code, 200)
        print "Network Destroy: OK"

        res = put('%s/api/Networks' % base, data={'name': 'Twitter', 'token': token4})
        self.assertEqual(res.status_code, 200)
        print "Load Real Graph: OK"

        res = post('%s/api/GetGraph' % base, data={'token': token4})
        self.assertEqual(res.status_code, 451)
        print "Get Graph (forbidden): OK"

        res = delete('%s/api/Experiment' % base, data={'token': token4})
        self.assertEqual(res.status_code, 200)

    def test_load_experiments(self):
        res = get('%s/api/Experiment' % base).json()
        token5 = res['token']
        self.assertIsNotNone(token5)

        res = get('%s/api/Generators' % base).json()
        endpoints = res['endpoints']

        for e in endpoints:
            if e['name'] == 'BAGraph':
                gr = put("%s%s" % (base, e['uri']), data={'n': 400, 'm': 3, 'token': token5})
                self.assertEqual(gr.status_code, 200)

        mods = get('%s/api/Models' % base).json()
        self.assertIn('endpoints', mods)
        print "Retrieve models enpoints: OK"

        # Models
        res = put('%s/api/SI' % base, data={'infected': 0.1, 'beta': 0.2, 'token': token5})
        self.assertEqual(res.status_code, 200)
        print "Load SI: OK"

        res = put('%s/api/SIS' % base, data={'infected': 0.1, 'beta': 0.2, 'lambda': 0.01, 'token': token5})
        self.assertEqual(res.status_code, 200)
        print "Load SIS: OK"

        res = put('%s/api/SIR' % base, data={'infected': 0.1, 'beta': 0.2, 'gamma': 0.01, 'token': token5})
        self.assertEqual(res.status_code, 200)
        print "Load SIR: OK"

        res = put('%s/api/Threshold' % base, data={'infected': 0.1, 'token': token5})
        self.assertEqual(res.status_code, 200)
        print "Load Threshold: OK"

        res = put('%s/api/KerteszThreshold' % base, data={'infected': 0.1, 'blocked': 0.1, 'adopter_rate': 0.1, 'token': token5})
        self.assertEqual(res.status_code, 200)
        print "Load KerteszThreshold: OK"

        res = put('%s/api/Profile' % base, data={'infected': 0.1, 'token': token5})
        self.assertEqual(res.status_code, 200)
        print "Load Profile: OK"

        res = put('%s/api/ProfileThreshold' % base, data={'infected': 0.1, 'token': token5})
        self.assertEqual(res.status_code, 200)
        print "Load ProfileThreshold: OK"

        res = put('%s/api/IndependentCascades' % base, data={'infected': 0.1, 'token': token5})
        self.assertEqual(res.status_code, 200)
        print "Load Independent Cascades: OK"

        res = post('%s/api/ExperimentStatus' % base, data={'token': token5}).json()
        self.assertEqual(len(res['Models']), 8)
        print "Display Experiment Resources: OK"

        res = delete('%s/api/Experiment' % base, data={'token': token5})
        self.assertEqual(res.status_code, 200)

    def test_experiment_execution(self):
        res = get('%s/api/Experiment' % base).json()
        token6 = res['token']
        self.assertIsNotNone(token6)

        res = get('%s/api/Generators' % base).json()
        endpoints = res['endpoints']

        for e in endpoints:
            if e['name'] == 'BAGraph':
                gr = put("%s%s" % (base, e['uri']), data={'n': 400, 'm': 3, 'token': token6})
                self.assertEqual(gr.status_code, 200)

        mods = get('%s/api/Models' % base).json()
        self.assertIn('endpoints', mods)
        print "Retrieve models enpoints: OK"

        # Models
        res = put('%s/api/SI' % base, data={'infected': 0.1, 'beta': 0.2, 'token': token6})
        self.assertEqual(res.status_code, 200)
        print "Load SI: OK"

        res = put('%s/api/SIS' % base, data={'infected': 0.1, 'beta': 0.2, 'lambda': 0.01, 'token': token6})
        self.assertEqual(res.status_code, 200)
        print "Load SIS: OK"

        res = put('%s/api/SIR' % base, data={'infected': 0.1, 'beta': 0.2, 'gamma': 0.01, 'token': token6})
        self.assertEqual(res.status_code, 200)
        print "Load SIR: OK"

        res = put('%s/api/Threshold' % base, data={'infected': 0.1, 'token': token6})
        self.assertEqual(res.status_code, 200)
        print "Load Threshold: OK"

        res = put('%s/api/KerteszThreshold' % base,
                  data={'infected': 0.1, 'blocked': 0.1, 'adopter_rate': 0.1, 'token': token6})
        self.assertEqual(res.status_code, 200)
        print "Load KerteszThreshold: OK"

        res = put('%s/api/Profile' % base, data={'infected': 0.1, 'token': token6})
        self.assertEqual(res.status_code, 200)
        print "Load Profile: OK"

        res = put('%s/api/ProfileThreshold' % base, data={'infected': 0.1, 'token': token6})
        self.assertEqual(res.status_code, 200)
        print "Load ProfileThreshold: OK"

        res = put('%s/api/IndependentCascades' % base, data={'infected': 0.1, 'token': token6})
        self.assertEqual(res.status_code, 200)
        print "Load Independent Cascades: OK"

        res = post('%s/api/ExperimentStatus' % base, data={'token': token6}).json()
        self.assertEqual(len(res['Models'].keys()), 8)
        print "Display Experiment Resources: OK"

        res = post('%s/api/Iteration' % base, data={'token': token6, 'models': ''}).json()
        self.assertEqual(len(res.keys()), 8)
        print "Single Iteration: OK"

        res = put('%s/api/ExperimentStatus' % base, data={'token': token6})
        self.assertEqual(res.status_code, 200)
        print "Experiment Reset: OK"

        res = post('%s/api/IterationBunch' % base, data={'bunch': 10, 'models': '', 'token': token6}).json()
        self.assertEqual(len(res.keys()), 8)
        print "Iteration Bunch: OK"

        res = put('%s/api/ExperimentStatus' % base, data={'token': token6})
        self.assertEqual(res.status_code, 200)
        print "Experiment Reset: OK"

        res = post('%s/api/CompleteRun' % base, data={'token': token6}).json()
        self.assertEqual(len(res.keys()), 8)
        print "Complete Run: OK"

        res = delete('%s/api/Networks' % base, data={'token': token6})
        self.assertEqual(res.status_code, 200)
        print "Network Destroy: OK"

        res = delete('%s/api/Models' % base, data={'token': token6})
        self.assertEqual(res.status_code, 200)
        print "Models Destroy: OK"

        res = delete('%s/api/Experiment' % base, data={'token': token6})
        self.assertEqual(res.status_code, 200)

    def test_advanced_configuration(self):
        res = get('%s/api/Experiment' % base).json()
        token = res['token']
        self.assertIsNotNone(token)

        res = get('%s/api/Generators' % base).json()
        endpoints = res['endpoints']

        for e in endpoints:
            if e['name'] == 'BAGraph':
                gr = put("%s%s" % (base, e['uri']), data={'n': 400, 'm': 3, 'token': token})
                self.assertEqual(gr.status_code, 200)

        mods = get('%s/api/Models' % base).json()
        self.assertIn('endpoints', mods)
        print "Retrieve models enpoints: OK"

        # Models
        res = put('%s/api/SI' % base, data={'infected': 0.1, 'beta': 0.2, 'token': token})
        self.assertEqual(res.status_code, 200)
        print "Load SI: OK"

        res = put('%s/api/SIS' % base, data={'infected': 0.1, 'beta': 0.2, 'lambda': 0.01, 'token': token})
        self.assertEqual(res.status_code, 200)
        print "Load SIS: OK"

        res = put('%s/api/SIR' % base, data={'infected': 0.1, 'beta': 0.2, 'gamma': 0.01, 'token': token})
        self.assertEqual(res.status_code, 200)
        print "Load SIR: OK"

        res = put('%s/api/Threshold' % base, data={'infected': 0.1, 'token': token})
        self.assertEqual(res.status_code, 200)
        print "Load Threshold: OK"

        res = put('%s/api/Profile' % base, data={'infected': 0.1, 'token': token})
        self.assertEqual(res.status_code, 200)
        print "Load Profile: OK"

        res = put('%s/api/ProfileThreshold' % base, data={'infected': 0.1, 'token': token})
        self.assertEqual(res.status_code, 200)
        print "Load ProfileThreshold: OK"

        res = put('%s/api/IndependentCascades' % base, data={'infected': 0.1, 'token': token})
        self.assertEqual(res.status_code, 200)
        print "Load Independent Cascades: OK"

        res = post('%s/api/ExperimentStatus' % base, data={'token': token}).json()
        self.assertEqual(len(res['Models']), 7)
        print "Display Experiment Resources: OK"

        res = post('%s/api/GetGraph' % base, data={'token': token}).json()
        self.assertNotEquals(res.keys(), 0)
        print "Get Graph: OK"

        conf = {'nodes': {'threshold': {}, 'profile': {}}, 'edges': [], 'model': {'initial_infected': []}}
        nds = []
        for n in res['nodes']:
            nid = n['id']
            nds.append(int(nid))
            th = np.random.random_sample()
            pr = np.random.random_sample()
            conf['nodes']['threshold'][nid] = th
            conf['nodes']['profile'][nid] = pr

        for e in res['links']:
            u = int(e['source'])
            v = int(e['target'])
            w = np.random.random_sample()
            conf['edges'].append({'source': u, 'target': v, 'weight': w})

        infected = np.random.choice(nds, len(nds)/10)
        conf['model']['initial_infected'] = list(infected)
        cs = json.dumps(conf)

        res = put('%s/api/Configure' % base, data={'status': cs, 'models': '', 'token': token})
        self.assertEqual(res.status_code, 200)
        print "Advanced Configuration: OK"

        res = post('%s/api/Iteration' % base, data={'token': token, 'models': ''}).json()
        self.assertEqual(len(res.keys()), 7)
        print "Single Iteration: OK"

        res = delete('%s/api/Experiment' % base, data={'token': token})
        self.assertEqual(res.status_code, 200)

    def test_exploratory(self):
        res = get('%s/api/Experiment' % base).json()
        token = res['token']
        self.assertIsNotNone(token)

        res = get('%s/api/Exploratory' % base)
        self.assertEqual(res.status_code, 200)
        print "List Exploratories: OK"

        res = post('%s/api/Exploratory' % base, data={'exploratory': 'Lastfm_rock', 'token': token})
        self.assertEqual(res.status_code, 200)
        print "Load Explortory: OK"

        res = put('%s/api/Threshold' % base, data={'infected': 0.1, 'token': token})
        self.assertEqual(res.status_code, 200)
        print "Load Threshold: OK"

        res = put('%s/api/Profile' % base, data={'infected': 0.1, 'token': token})
        self.assertEqual(res.status_code, 200)
        print "Load Profile: OK"

        res = put('%s/api/ProfileThreshold' % base, data={'infected': 0.1, 'token': token})
        self.assertEqual(res.status_code, 200)
        print "Load ProfileThreshold: OK"

        res = put('%s/api/IndependentCascades' % base, data={'infected': 0.1, 'token': token})
        self.assertEqual(res.status_code, 200)
        print "Load Independent Cascades: OK"

        res = post('%s/api/Iteration' % base, data={'token': token, 'models': ''}).json()
        self.assertEqual(len(res.keys()), 4)
        print "Single Iteration: OK"

        res = delete('%s/api/Experiment' % base, data={'token': token})
        self.assertEqual(res.status_code, 200)

    def test_upload_graph(self):
        res = get('%s/api/Experiment' % base).json()
        token = res['token']
        g = nx.barabasi_albert_graph(100000, 4)
        js = json_graph.node_link_data(g)
        jd = json.dumps(js)
        res = put('http://localhost:5000/api/UploadNetwork', data={'file': str(jd), 'directed': False, 'token': token})
        self.assertEqual(res.status_code, 200)
        res = post('%s/api/GetGraph' % base, data={'token': token}).json()
        self.assertNotEquals(res.keys(), 0)
        res = delete('%s/api/Experiment' % base, data={'token': token})
        self.assertEqual(res.status_code, 200)

if __name__ == '__main__':
    unittest.main()
