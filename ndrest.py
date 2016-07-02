from flask import Flask, request
import shelve
import os
from flask.ext.cors import CORS
from flask_restful import Resource, Api
from flask_apidoc import ApiDoc
from ndlib import ThresholdModel as tm
from ndlib import SIRModel as sir
from ndlib import SIModel as si
from ndlib import SISModel as sis
from ndlib import ProfileModel as ac
from ndlib import ProfileThresholdModel as pt
from ndlib import IndependentCascadesModel as ic
from ndlib import VoterModel as vm
from ndlib import MajorityRuleModel as mrm
from ndlib import SznajdModel as sm
import json
import networkx as nx
from networkx.readwrite import json_graph
import uuid

__author__ = "Giulio Rossetti"
__email__ = "giulio.rossetti@gmail.com"

app = Flask(__name__)
api = Api(app)
doc = ApiDoc(app=app)
CORS(app)

max_number_of_nodes = 100000

# Status code
success = 200
created = 201
bad_request = 400
unauthorized = 401
forbidden = 403
not_found = 404
unavailable = 451
not_implemented = 501


class Experiment(Resource):
    """
    @apiDefine Experiment Experiment
            An experiment represents the analytical unit of this REST API, it is composed by:
                <ul>
                    <li>A single network</li>
                    <li>One or more diffusion models</li>
                </ul>
            In order to perform an experiment the user should:
                <ol>
                    <li><a href="#api-Experiment-getexp">Request a token</a>, which univocally identifies the experiment</li>
                    <li><a href="#api-Resources">Select</a> and <a href="#api-Networks">load</a> resource using a
                    Network Generator or loading an existing Graph</li>
                    <li><a href="#api-Models">Select</a> one, or more, diffusion model(s)</li>
                    <li>(optional) Use the <a href="#api-Experiment-configure">advanced configuration</a> facilities</li>
                    <li><a href="#api-Iterators">Execute</a> the simulation</li>
                    <li>(optional) <a href="#api-Experiment-resetexp">Reset</a> the experiment status, modify the models/network</li>
                    <li><a href="#api-Experiment-deleteexp">Destroy</a> the experiment </li>
                </ol>
    """

    def get(self):
        """
            @api {get} /api/Experiment Create
            @ApiDescription Setup a new experiment and generate a its unique identifier.
                An experiment is described by the Network (only one) and Models associated to it.
            @apiVersion 0.1.0
            @apiName getexp
            @apiGroup Experiment
            @apiSuccess {String}    token              The token identifying the experiment.
            @apiExample [python request] Example usage:
                        get('http://localhost:5000/api/Experiment')
        """

        token = str(uuid.uuid4())
        db = shelve.open("data/db/%s" % token)
        db[token] = {'net': None, 'models': {}}
        db.close()

        return {'token': token}, success

    def delete(self):
        """
            @api {delete} /api/Experiment Destroy
            @ApiDescription Delete all the resources (the network and the models) attached to the specified experiment.
            @apiVersion 0.1.0
            @apiParam {String} token    The token identifying the experiment.
            @apiName deleteexp
            @apiGroup Experiment
            @apiExample [python request] Example usage:
                        delete('http://localhost:5000/api/Experiment', data={'token': token})
        """
        token = str(request.form['token'])
        try:
            os.remove("data/db/%s" % token)
        except:
            return {"Message": "Wrong Token"}, bad_request

        return {'Message': "Experiment Destroyed"}, success


class ExperimentStatus(Resource):

    def post(self):
        """
            @api {post} /api/ExperimentStatus Describe
            @ApiDescription Describe the resources (Network and Models) involved in the experiment.
            @apiVersion 0.1.0
            @apiName describeexp
            @apiGroup Experiment
            @apiParam {String}  token The token identifying the experiment.
            @apiExample {python} [Python request] Example usage:
                        post('http://localhost:5000/api/ExperimentStatus')
        """
        token = str(request.form['token'])
        db = shelve.open("data/db/%s" % token)

        if token not in db:
            return {"Message": "Wrong Token"}, bad_request

        exp = db[token]

        try:
            net_info = {k: v for k, v in exp['net'].iteritems() if k != 'g'}
            models = {mname: exp['models'][mname].getinfo() for mname in exp['models']}
            result = {'Network': net_info, 'Models': models}
            db.close()
            return result
        except:
            db.close()
            return {'Message': 'No resources attached to this token'}, not_found

    def put(self):
        """
            @api {put} /api/ExperimentStatus Reset
            @ApiDescription Reset the status of models attached to the specified experiment.
                            If no models are specified all the current experiment statuses will be reset.
            @apiVersion 0.1.0
            @apiParam {String}  token   The token identifying the experiment.
            @apiParam {String}  models  String of comma separated model names.
            @apiName resetexp
            @apiGroup Experiment
            @apiExample [python request] Example usage:
                        put('http://localhost:5000/api/ExperimentStatus', data={'token': token, 'models': 'model1,model2'})
        """
        token = str(request.form['token'])
        db = shelve.open("data/db/%s" % token)

        if token not in db:
            db.close()
            return {"Message": "Wrong Token"}, bad_request

        ml = []
        if 'models' in request.form:
            ml = request.form['models'].split(',')

        try:
            ml = {c: db[token]['models'][c] for c in ml if c != ''}

            mods = ml if len(ml) > 0 else db[token]['models'].keys()

            for mname in mods:
                m = db[token]['models'][mname]
                m.reset()
                m.set_initial_status()
                del db[token]['models'][mname]
                db[token]['models'][mname] = m
        except:
            db.close()
            return {'Message': 'Parameter error'}, bad_request
        db.close()
        return {'Message': 'Experiment cleaned'}, success


#######################################################################################

class Graph(Resource):

    def post(self):
        """
            @api {post} /api/GetGraph  Get Network
            @ApiDescription Return the json representation of the network analyzed
            @apiVersion 0.5.0
            @apiName expgraphs
            @apiGroup Networks
            @apiParam  token   The token
            @apiSuccessExample {json} Response example:
                {
                "directed": false,
                "graph": {
                    "name": "barabasi_albert_graph(5,1)"
                },
                "links": [
                    {
                        "source": 0,
                        "target": 1
                    },
                    {
                        "source": 0,
                        "target": 2
                    },
                    {
                        "source": 0,
                        "target": 3
                    },
                    {
                        "source": 0,
                        "target": 4
                    }
                ],
                "multigraph": false,
                "nodes": [
                    {
                        "id": 0
                    },
                    {
                        "id": 1
                    },
                    {
                        "id": 2
                    },
                    {
                        "id": 3
                    },
                    {
                        "id": 4
                    }
                ]
            }
            @apiExample [python request] Example usage:
                        post('http://localhost:5000/api/GetGraph'data={'token': token})
        """

        token = str(request.form['token'])
        db = shelve.open("data/db/%s" % token)         
        if token not in db:
            db.close()
            return {"Message": "Wrong Token"}, bad_request

        try:
            res = json.load(open("resources/networks.json"))['networks']
            available = True
            for net in res:
                if net['name'] == db[token]['net']['name']:
                    available = net['open_access']
                    break

            if available:
                g = db[token]['net']['g']
                res = json_graph.node_link_data(g)
            else:
                db.close()
                return {"Message": "Dataset in read-only access."}, unavailable
        except:
            db.close()
            return {"Message": "No graph resource assigned to the experiment"}, not_found

        db.close()
        return res, success


class Resources(Resource):
    """
        @apiDefine Resources Resources
                Endpoints belonging to this family provide access to resources, networks and models, listing and lookup
                facilities.</br>
                They also handle the destruction phase of experiment resources.
    """


class Networks(Resource):
    """
        @apiDefine Networks Networks
                Endpoints belonging to this family provide access to network resources.</br>
                In particular they provide lookup facilities for both real world datasets and network generators. </br>
                Moreover, the <a href="#api-Networks-expgraphs">Get Network</a> endpoint allows for the download of
                synthetic (i.e., generated) networks as well as all of those datasets for which are not specified access
                restriction.
    """

    def get(self):
        """
            @api {get} /api/Networks  Real Networks Endpoints
            @ApiDescription Return the available network endpoints and their parameters
            @apiVersion 0.4.0
            @apiName getgraphs
            @apiGroup Resources
            @apiSuccess {Object}    endpoints              List of network endpoints.
            @apiSuccessExample {json} Response example: Available networks
                {'networks':
                    [
                        {
                            'name': 'Lastfm',
                            'size':
                                {
                                    'nodes': 70000,
                                    'edges': 389639
                                },
                            'description': 'Undirected social graph involving UK users of Last.fm'
                        }
                    ]
                }
            @apiExample [python request] Example usage:
                        get('http://localhost:5000/api/Networks')
        """
        res = json.load(open("resources/networks.json"))
        return res, success

    def put(self):
        """
            @api {put} /api/Networks Load real graph
            @ApiDescription Create an ER graph compliant to the specified parameters and bind it to the provided token
            @apiVersion 0.4.0
            @apiParam {String} token    The token.
            @apiParam {String} name    The network name.
            @apiName loadgraph
            @apiGroup Networks
            @apiExample [python request] Example usage:
            put('http://localhost:5000/api/Networks', data={'name': 'Last.fm','token': token})
        """
        token = str(request.form['token'])
        db = shelve.open("data/db/%s" % token)
        
        if token not in db:
            db.close()
            return {"Message": "Wrong Token"}, bad_request

        directed = False
        name = request.form['name']
        nets = json.load(open("resources/networks.json"))['networks']
        for net in nets:
            if net["name"] == name:
                directed = net["directed"]
                break

        g = None
        if directed:
            g = nx.DiGraph()
        else:
            g = nx.Graph()
        try:
            f = open("data/networks/%s.csv" % name)
            for l in f:
                l = map(int, l.rstrip().split(","))
                g.add_edge(l[0], l[1])

            r = db[token]
            r['net'] = {'g': g, 'name': name}
            db[token] = r
            db.close()
            return {'Message': 'Network correctly loaded'}, success
        except:
            db.close()
            return {'Message': "Wrong network name."}, bad_request

    def delete(self):
        """
            @api {delete} /api/Networks  Network Destroy
            @ApiDescription Delete the graph resource attached to the specified token
            @apiVersion 0.4.0
            @apiParam {String} token    The token.
            @apiName destroynetwork
            @apiGroup Resources
            @apiExample [python request] Example usage:
                        delete('http://localhost:5000/api/Networks', data={'token': token})
        """
        token = str(request.form['token'])
        db = shelve.open("data/db/%s" % token)         

        if token not in db:
            db.close()
            return {"Message": "Wrong Token"}, bad_request

        del db[token]['net']
        db[token]['net'] = {}
        db.close()
        return {'Message': 'Resource deleted'}, success


class Generators(Resource):

    def get(self):
        """
            @api {get} /api/Generators  Network Generator Endpoints
            @ApiDescription Return the available network endpoints and their parameters
            @apiVersion 0.1.0
            @apiName getnetworks
            @apiGroup Resources
            @apiSuccess {Object}    endpoints              List of network endpoints.
            @apiSuccessExample {json} Response example: Endpoint List
                {'endpoints':
                    [
                        {
                            'name': 'Erdos Reny',
                            'uri': 'http://localhost:5000/api/Networks/ERGraph',
                            'params':
                                {
                                    'token': 'access token',
                                    'n': 'number of nodes',
                                    'p': 'rewiring probability'
                                }
                        },
                        {
                            'name': 'Barabasi Albert',
                            'uri': 'http://localhost:5000/api/Networks/BarabasiAlbertGraph',
                            'params':
                                {
                                    'token': 'access token',
                                    'n': 'number of nodes',
                                    'm': 'Number of edges to attach from a new node to existing nodes'
                                }
                        }
                    ]
                }
            @apiExample [python request] Example usage:
                        get('http://localhost:5000/api/Generators')
        """
        res = json.load(open("resources/generators.json"))
        return res, success


class ERGraph(Resource):

    def put(self):
        """
            @api {put} /api/Generators/ERGraph Erdos-Renyi
            @ApiDescription Create an ER graph compliant to the specified parameters and bind it to the provided token
            @apiVersion 0.1.0
            @apiParam {String} token    The token.
            @apiParam {Number{200..100000}} n    The number of nodes.
            @apiParam {Number{0-1}} p    The rewiring probability.
             @apiParam {Boolean} directed    If the graph should be directed.
             If not specified an undirected graph will be generated.
            @apiName ERGraph
            @apiGroup Networks
            @apiExample [python request] Example usage:
            put('http://localhost:5000/api/Generators/ERGraph', data={'n': n, 'p': p, 'token': token})
        """
        token = str(request.form['token'])
        db = shelve.open("data/db/%s" % token)         

        if token not in db:
            db.close()
            return {"Message": "Wrong Token"}, bad_request

        n = int(request.form['n'])
        if n < 200 or n > max_number_of_nodes:
            db.close()
            return {"Message": "Node number out fo range."}, bad_request

        try:
            p = float(request.form['p'])
            directed = False
            if 'directed' in request.form:
                directed = bool(request.form['directed'])

            g = nx.erdos_renyi_graph(n, p, directed)

            r = db[token]
            r['net'] = {'g': g, 'name': 'ERGraph', 'params': {'n': n, 'p': p}}
            db[token] = r
        except:
            db.close()
            return {'Message': 'Parameter error'}, bad_request

        db.close()
        return {'Message': 'Resource created'}, success


class BarabasiAlbertGraph(Resource):

    def put(self):
        """
            @api {put} /api/Generators/BarabasiAlbertGraph Barabasi-Albert
            @ApiDescription Create a BA graph compliant to the specified parameters and bind it to the provided token
            @apiVersion 0.2.0
            @apiParam {String} token    The token.
            @apiParam {Number{200..100000}} n    The number of nodes.
            @apiParam {Number{1..}} m    The number of edges attached to each new node.
            @apiName BAGraph
            @apiGroup Networks
            @apiExample [python request] Example usage:
            put('http://localhost:5000/api/Generators/BarabasiAlbertGraph', data={'n': n, 'm': m, 'token': token})
        """
        token = str(request.form['token'])
        db = shelve.open("data/db/%s" % token)

        if token not in db:
            db.close()
            return {"Message": "Wrong Token"}, bad_request

        n = int(request.form['n'])
        if n < 200 or n > max_number_of_nodes:
            db.close()
            return {"Message": "Node number out fo range."}, bad_request

        try:
            m = int(request.form['m'])
            g = nx.barabasi_albert_graph(n, m)

            r = db[token]
            r['net'] = {'g': g, 'name': 'BAGraph', 'params': {'n': n, 'm': m}}
            db[token] = r
        except:
            db.close()
            return {'Message': 'Parameter error'}, bad_request
        db.close()
        return {'Message': 'Resource created'}, success


class WattsStrogatzGraph(Resource):

    def put(self):
        """
            @api {put} /api/Generators/WattsStrogatzGraph Watts-Strogatz
            @ApiDescription Create a WS graph compliant to the specified parameters and bind it to the provided token
            @apiVersion 0.3.0
            @apiParam {String} token    The token.
            @apiParam {Number{200..100000}} n    The number of nodes.
            @apiParam {Number{1..}} k    Each node is connected to k nearest neighbors in ring topology
            @apiParam {Number{0-1}} p    The probability of rewiring each edge
            @apiName WSGraph
            @apiGroup Networks
            @apiExample [python request] Example usage:
            put('http://localhost:5000/api/Generators/WattsStrogatzGraph', data={'n': n, 'k': k, 'p': p, 'token': token})
        """
        token = str(request.form['token'])
        db = shelve.open("data/db/%s" % token)

        if token not in db:
            db.close()
            return {"Message": "Wrong Token"}, bad_request

        n = int(request.form['n'])
        if n < 200 or n > max_number_of_nodes:
            db.close()
            return {"Message": "Node number out fo range."}, bad_request

        try:
            k = int(request.form['k'])
            p = float(request.form['p'])
            g = nx.watts_strogatz_graph(n, k, p)

            r = db[token]
            r['net'] = {'g': g, 'name': 'WSGraph', 'params': {'n': n, 'k': k, 'p': p}}
            db[token] = r
        except:
            db.close()
            return {'Message': 'Parameter error'}, bad_request
        db.close()
        return {'Message': 'Resource created'}, success


#######################################################################################


class Models(Resource):
    """
        @apiDefine Models Models
                Endpoints belonging to this family provide access to model resources.
    """

    def get(self):
        """
            @api {get} /api/Models Models Endpoints
            @ApiDescription Return the available models endpoints and their parameter specification
            @apiVersion 0.1.0
            @apiName getmodellist
            @apiGroup   Resources
            @apiSuccess {Object}    endpoints              List of model endpoints.
            @apiSuccessExample {json} Response example: Endpoint List
                {'endponts':
                    [
                        {
                            'name': 'Threshold',
                            'uri': 'http://localhost:5000/api/Models/Threshold',
                            'params':
                                {
                                    'token': 'access token',
                                }
                        },
                        {
                            'name': 'SIR',
                            'uri': 'http://localhost:5000/api/Models/SIR',
                            'params':
                                {
                                    'token': 'access token',
                                }
                        }
                    ]
                }
            @apiExample [python request] Example usage:
                        get('http://localhost:5000/api/Models')
        """
        res = json.load(open("resources/models.json"))
        return res, success

    def delete(self):
        """
            @api {delete} /api/Models Models Destroy
            @ApiDescription Delete model resources attached to the specified token.
                            If no models are specified all the ones bind to the experiment will be destroyed.
            @apiVersion 0.1.0
            @apiParam {String} token    The token.
            @apiParam {String} models String composed by comma separated model names.
            @apiName deletemodels
            @apiGroup Resources
            @apiExample [python request] Example usage:
                        delete('http://localhost:5000/api/Models', data={'token': token, 'models': 'model1,model2'})
        """

        token = str(request.form['token'])
        db = shelve.open("data/db/%s" % token)

        if token not in db:
            db.close()
            return {"Message": "Wrong Token"}, bad_request
        try:
            ml = []
            if 'models' in request.form:
                ml = request.form['models'].split(',')

            ml = {c: db[token]['models'][c] for c in ml if c != ''}
            mods = ml if len(ml) > 0 else db[token]['models'].keys()

            for mname in mods:
                del db[token]['models'][mname]
        except:
            db.close()
            return {'Message': 'Parameter error'}, bad_request

        db.close()
        return {'Message': 'Resource destroyed'}, success


class Configure(Resource):

    def put(self):
        """
            @api {put} /api/Configure Advanced Configuration
            @ApiDescription This endpoint allows for an in-depth specification of the planned experiment.
                            The advanced configuration regards:
                            <ul>
                                <li>Specification of the set of initially infected nodes</li>
                                <li>Specification of nodes/edges weights (i.e., individual threshold/profile)</li>
                            </ul>
                            The configuration will be applied to all the models attached to the experiment
                            (if not specified otherwise). </br> </br>
                            <u>Pay attention</u>: this endpoint should be called only after having instantiated both
                            Network and Model
                            resources.
            @apiVersion 0.5.0
            @apiParam {String}  token   The token.
            @apiParam {String}  models  String composed by comma separated model names.
            @apiParam {json} status JSON description of the node/edge attributes.
            @apiParamExample {json} Expected JSON Input (could be partially filled)
                {
                    'nodes':
                        {
                        'threshold': {"node1": 0.1, "node2": 0.05, "node3": 0.24 },
                        'profile': {"node1": 0.4, "node2": 0.5, "node3": 0.64}
                        },
                    'edges':
                        [
                            {
                                "source": "node1",
                                "target": "node2",
                                "weight": 0.2
                            },
                            {
                                "source": "node2",
                                "target": "node3",
                                "weight": 0.7
                            },
                        ],
                    'model': {'initial_infected': [node1, node3]}
                }
            @apiName configure
            @apiGroup Experiment
            @apiExample [python request] Example usage:
            put('http://localhost:5000/api/Configure', data={'status': json, 'models': 'model1,model2','token': token})
        """
        token = str(request.form['token'])
        db = shelve.open("data/db/%s" % token)

        if token not in db:
            db.close()
            return {"Message": "Wrong Token"}, bad_request

        try:
            status = json.loads(request.form['status'])
        except:
            db.close()
            return {"Message": "Value Error: No JSON object could be decoded"}, bad_request

        try:
            ml = request.form['models'].split(',')
            ml = {c: db[token]['models'][c] for c in ml if c != ''}
            models = ml if len(ml) > 0 else db[token]['models'].keys()

            for model_name in models:
                db[token]['models'][model_name].set_initial_status(status)
        except:
            db.close()
            return {'Message': 'Parameter error'}, bad_request

        db.close()
        return {"Message": "Configuration applied"}, success


class Threshold(Resource):

    def put(self):
        """
            @api {put} /api/Threshold Threshold
            @ApiDescription Instantiate a Threshold Model on the network bound to the provided token.
            @apiVersion 0.1.0
            @apiParam {String} token    The token.
            @apiParam {Number{0-1}} threshold    A fixed threshold value for all the nodes: if not specified the
                                                thresholds will be assigned using a normal distribution.
            @apiParam {Number{0-1}} infected    The initial percentage of infected nodes.
            @apiName threshold
            @apiGroup Models
            @apiExample [python request] Example usage:
            put('http://localhost:5000/api/Threshold', data={'token': token, 'infected': percentage})
        """
        token = str(request.form['token'])
        db = shelve.open("data/db/%s" % token)

        if token not in db:
            db.close()
            return {"Message": "Wrong Token"}, bad_request

        infected = 0.05
        if 'infected' in request.form and request.form['infected'] != "":
            infected = request.form['infected']

        threshold = 0
        if 'threshold' in request.form and request.form['threshold'] != "":
            threshold = request.form['threshold']

        g = db[token]['net']['g']

        model = tm.ThresholdModel(g)
        conf = {'model': {'percentage_infected': float(infected)}}

        if float(threshold) > 0:
            conf['nodes'] = {'threshold': {}}
            for n in g.nodes():
                conf['nodes']['threshold'][str(n)] = float(threshold)

        model.set_initial_status(conf)

        if 'configuration' in db[token]:
            model.set_initial_status(db[token]['configuration'])

        try:
            r = db[token]
            keys = r['models'].keys()
            if len(keys) > 0:
                mid = len([int(x.split("_")[1]) for x in keys if 'Threshold' == x.split("_")[0]])
                r['models']['Threshold_%s' % mid] = model
            else:
                r['models']['Threshold_0'] = model
            db[token] = r
        except:
            db.close()
            return {'Message': 'Parameter error'}, bad_request

        db.close()
        return {'Message': 'Resource created'}, success


class IndependentCascades(Resource):

    def put(self):
        """
            @api {put} /api/IndependentCascades Independent Cascades
            @ApiDescription Instantiate an Independent Cascades Model on the network bound to the provided token.
                The edge threshold for each node is assumed equal to 1 divided its number of neighbors:
                this behavior can be changed by using the <a href"#api-Experiment-configure">advanced
                configuration</a> endpoint.
            @apiVersion 0.5.0
            @apiParam {String} token    The token.
            @apiParam {Number{0-1}} infected    The initial percentage of infected nodes.
            @apiName indepcascades
            @apiGroup Models
            @apiExample [python request] Example usage:
            put('http://localhost:5000/api/IndependentCascades', data={'token': token, 'infected': percentage})
        """
        token = str(request.form['token'])
        db = shelve.open("data/db/%s" % token)
        if token not in db:
            db.close()
            return {"Message": "Wrong Token"}, bad_request

        infected = request.form['infected']
        if infected == '':
            infected = 0.05

        g = db[token]['net']['g']
        model = ic.IndependentCascadesModel(g)
        model.set_initial_status({'model': {'percentage_infected': float(infected)}})

        if 'configuration' in db[token]:
            model.set_initial_status(db[token]['configuration'])

        try:
            r = db[token]
            keys = r['models'].keys()
            if len(keys) > 0:
                mid = len([int(x.split("_")[1]) for x in keys if 'IndependentCascades' == x.split("_")[0]])
                r['models']['IndependentCascades_%s' % mid] = model
            else:
                r['models']['IndependentCascades_0'] = model
            db[token] = r
        except:
            db.close()
            return {'Message': 'Parameter error'}, bad_request

        db.close()
        return {'Message': 'Resource created'}, success


class SIR(Resource):

    def put(self):
        """
            @api {put} /api/SIR SIR
            @ApiDescription Instantiate a SIR Model on the network bound to the provided token.
            @apiVersion 0.2.0
            @apiParam {String} token    The token.
            @apiParam {Number{0-1}} infected    The initial percentage of infected nodes.
            @apiParam {Number{0-1}}  beta    Infection rate.
            @apiParam {Number{0-1}} gamma    Recovery rate.
            @apiName sir
            @apiGroup Models
            @apiExample [python request] Example usage:
            put('http://localhost:5000/api/SIR', data={'beta': beta, 'gamma': gamma, 'infected': percentage, 'token': token})
        """
        token = str(request.form['token'])
        db = shelve.open("data/db/%s" % token)

        if token not in db:
            db.close()
            return {"Message": "Wrong Token"}, bad_request

        try:
            beta = request.form['beta']
            gamma = request.form['gamma']
            infected = request.form['infected']
            if infected == '':
                infected = 0.05

            g = db[token]['net']['g']
            model = sir.SIRModel(g, {'beta': float(beta), 'gamma': float(gamma)})
            model.set_initial_status({'model': {'percentage_infected': float(infected)}})

            if 'configuration' in db[token]:
                model.set_initial_status(db[token]['configuration'])

            r = db[token]
            keys = r['models'].keys()
            if len(keys) > 0:
                mid = len([int(x.split("_")[1]) for x in keys if 'SIR' == x.split("_")[0]])
                r['models']['SIR_%s' % mid] = model
            else:
                r['models']['SIR_0'] = model
            db[token] = r
        except:
            db.close()
            return {'Message': 'Parameter error'}, bad_request

        db.close()
        return {'Message': 'Resource created'}, success


class SI(Resource):

    def put(self):
        """
            @api {put} /api/SI SI
            @ApiDescription Instantiate a SI Model on the network bound to the provided token.
            @apiVersion 0.2.0
            @apiParam {String} token    The token.
            @apiParam {Number{0-1}} infected    The initial percentage of infected nodes.
            @apiParam {Number{0-1}}  beta    Infection rate.
            @apiName si
            @apiGroup Models
            @apiExample [python request] Example usage:
            put('http://localhost:5000/api/SI', data={'beta': beta, 'infected': percentage, 'token': token})
        """
        token = str(request.form['token'])
        db = shelve.open("data/db/%s" % token)

        if token not in db:
            db.close()
            return {"Message": "Wrong Token"}, bad_request

        try:
            beta = request.form['beta']
            infected = request.form['infected']
            if infected == '':
                infected = 0.05

            g = db[token]['net']['g']
            model = si.SIModel(g, {'beta': float(beta)})
            model.set_initial_status({'model': {'percentage_infected': float(infected)}})

            if 'configuration' in db[token]:
                model.set_initial_status(db[token]['configuration'])

            r = db[token]
            keys = r['models'].keys()
            if len(keys) > 0:
                mid = len([int(x.split("_")[1]) for x in keys if 'SI' == x.split("_")[0]])
                r['models']['SI_%s' % mid] = model
            else:
                r['models']['SI_0'] = model
            db[token] = r
        except:
            db.close()
            return {'Message': 'Parameter error'}, bad_request

        db.close()
        return {'Message': 'Resource created'}, success


class SIS(Resource):

    def put(self):
        """
            @api {put} /api/SIS SIS
            @ApiDescription Instantiate a SIS Model on the network bound to the provided token.
            @apiVersion 0.2.0
            @apiParam {String} token    The token.
            @apiParam {Number{0-1}} infected    The initial percentage of infected nodes.
            @apiParam {Number{0-1}}  beta    Infection rate.
            @apiParam {Number{0-1}}  lambda    Recovery rate.
            @apiName sis
            @apiGroup Models
            @apiExample [python request] Example usage:
            put('http://localhost:5000/api/SIS', data={'beta': beta, 'lambda': lambda, 'infected': percentage, 'token': token})
        """
        token = str(request.form['token'])
        db = shelve.open("data/db/%s" % token)

        if token not in db:
            db.close()
            return {"Message": "Wrong Token"}, bad_request

        try:
            beta = request.form['beta']
            lamb = request.form['lambda']
            infected = request.form['infected']
            if infected == '':
                infected = 0.05

            g = db[token]['net']['g']
            model = sis.SISModel(g, {'beta': float(beta), 'lambda': float(lamb)})
            model.set_initial_status({'model': {'percentage_infected': float(infected)}})

            if 'configuration' in db[token]:
                model.set_initial_status(db[token]['configuration'])

            r = db[token]
            keys = r['models'].keys()
            if len(keys) > 0:
                mid = len([int(x.split("_")[1]) for x in keys if 'SIS' == x.split("_")[0]])
                r['models']['SIS_%s' % mid] = model
            else:
                r['models']['SIS_0'] = model
            db[token] = r
        except:
            db.close()
            return {'Message': 'Parameter error'}, bad_request

        db.close()
        return {'Message': 'Resource created'}, success


class Profile(Resource):

    def put(self):
        """
            @api {put} /api/Profile Profile
            @ApiDescription Instantiate a Profile Model on the network bound to the provided token.
            @apiVersion 0.3.0
            @apiParam {String} token    The token.
            @apiParam {Number{0-1}} profile    A fixed profile value for all the nodes: if not specified the
                                                profile will be assigned using a normal distribution.

            @apiParam {Number{0-1}} infected    The initial percentage of infected nodes.
            @apiName profile
            @apiGroup Models
            @apiExample [python request] Example usage:
            put('http://localhost:5000/api/Profile', data={'token': token, 'infected': percentage})
        """
        token = str(request.form['token'])
        db = shelve.open("data/db/%s" % token)

        if token not in db:
            db.close()
            return {"Message": "Wrong Token"}, bad_request

        profile = 0
        if 'profile' in request.form and request.form['profile'] != "":
            profile = float(request.form['profile'])

        try:
            infected = request.form['infected']
            if infected == '':
                infected = 0.05

            g = db[token]['net']['g']
            model = ac.ProfileModel(g)
            conf = {'model': {'percentage_infected': float(infected)}}

            if float(profile) > 0:
                conf['nodes'] = {'profile': {}}
                for n in g.nodes():
                    conf['nodes']['profile'][str(n)] = float(profile)

            model.set_initial_status(conf)

            if 'configuration' in db[token]:
                model.set_initial_status(db[token]['configuration'])

            r = db[token]
            keys = r['models'].keys()
            if len(keys) > 0:
                mid = len([int(x.split("_")[1]) for x in keys if 'Profile' == x.split("_")[0]])
                r['models']['Profile_%s' % mid] = model
            else:
                r['models']['Profile_0'] = model
            db[token] = r
        except:
            db.close()
            return {'Message': 'Parameter error'}, bad_request

        db.close()
        return {'Message': 'Resource created'}, success


class ProfileThreshold(Resource):

    def put(self):
        """
            @api {put} /api/ProfileThreshold Profile-Threshold
            @ApiDescription Instantiate a Profile-Threshold Model on the network bound to the provided token.
            @apiVersion 0.3.0
            @apiParam {String} token    The token.
            @apiParam {Number{0-1}} profile    A fixed profile value for all the nodes: if not specified the
                                                profile will be assigned using a normal distribution.
            @apiParam {Number{0-1}} threshold    A fixed threshold value for all the nodes: if not specified the
                                                thresholds will be assigned using a normal distribution.
            @apiParam {Number{0-1}} infected    The initial percentage of infected nodes.
            @apiName profilethreshold
            @apiGroup Models
            @apiExample [python request] Example usage:
            put('http://localhost:5000/api/ProfileThreshold', data={'token': token, 'infected': percentage})
        """
        token = str(request.form['token'])
        db = shelve.open("data/db/%s" % token)

        if token not in db:
            db.close()
            return {"Message": "Wrong Token"}, bad_request

        threshold = 0
        if 'threshold' in request.form and request.form['threshold'] != "":
            threshold = request.form['threshold']

        profile = 0
        if 'profile' in request.form and request.form['profile'] != "":
            profile = request.form['profile']

        try:
            infected = request.form['infected']
            if infected == '':
                infected = 0.05

            g = db[token]['net']['g']
            model = pt.ProfileThresholdModel(g)
            conf = {'model': {'percentage_infected': float(infected)}}

            if float(profile) > 0:
                conf['nodes'] = {'profile': {}}
                for n in g.nodes():
                    conf['nodes']['profile'][str(n)] = float(profile)

            if float(threshold) > 0:
                if 'nodes' not in conf:
                    conf['nodes'] = {'threshold': {}}
                else:
                    conf['nodes']['threshold'] = {}

                for n in g.nodes():
                    conf['nodes']['threshold'][str(n)] = float(threshold)

            model.set_initial_status(conf)

            if 'configuration' in db[token]:
                model.set_initial_status(db[token]['configuration'])

            r = db[token]
            keys = r['models'].keys()
            if len(keys) > 0:
                mid = len([int(x.split("_")[1]) for x in keys if 'ProfileThreshold' == x.split("_")[0]])
                r['models']['ProfileThreshold_%s' % mid] = model
            else:
                r['models']['ProfileThreshold_0'] = model
            db[token] = r
        except:
            db.close()
            return {'Message': 'Parameter error'}, bad_request

        db.close()
        return {'Message': 'Resource created'}, success


class Voter(Resource):

    def put(self):
        """
            @api {put} /api/Voter Voter
            @ApiDescription Instantiate the Voter Model on the network bound to the provided token.
            @apiVersion 0.7.0
            @apiParam {String} token    The token.
            @apiParam {Number{0-1}} infected    The initial percentage of infected nodes.
            @apiName voter
            @apiGroup Models
            @apiExample [python request] Example usage:
            put('http://localhost:5000/api/Voter', data={'token': token, 'infected': percentage})
        """
        token = str(request.form['token'])
        db = shelve.open("data/db/%s" % token)
        if token not in db:
            db.close()
            return {"Message": "Wrong Token"}, bad_request

        infected = request.form['infected']
        if infected == '':
            infected = 0.05

        g = db[token]['net']['g']
        model = vm.VoterModel(g)
        model.set_initial_status({'model': {'percentage_infected': float(infected)}})

        if 'configuration' in db[token]:
            model.set_initial_status(db[token]['configuration'])

        try:
            r = db[token]
            keys = r['models'].keys()
            if len(keys) > 0:
                mid = len([int(x.split("_")[1]) for x in keys if 'VoterModel' == x.split("_")[0]])
                r['models']['VoterModel_%s' % mid] = model
            else:
                r['models']['VoterModel_0'] = model
            db[token] = r
        except:
            db.close()
            return {'Message': 'Parameter error'}, bad_request

        db.close()
        return {'Message': 'Resource created'}, success


class MaJorityRule(Resource):

    def put(self):
        """
            @api {put} /api/MajorityRule Majority Rule
            @ApiDescription Instantiate the Majority Rule Model on the network bound to the provided token.
            @apiVersion 0.7.0
            @apiParam {String} token    The token.
            @apiParam {Number{0-1}} infected    The initial percentage of infected nodes.
            @apiParam {Number{0-N}} q The group size.
            @apiName majority
            @apiGroup Models
            @apiExample [python request] Example usage:
            put('http://localhost:5000/api/Majority', data={'token': token, 'infected': percentage, 'q': q})
        """
        token = str(request.form['token'])
        db = shelve.open("data/db/%s" % token)
        if token not in db:
            db.close()
            return {"Message": "Wrong Token"}, bad_request

        infected = request.form['infected']
        if infected == '':
            infected = 0.05

        try:
            q = int(request.form['q'])
        except:
            db.close()
            return {"Message": "Parameter error"}, bad_request

        g = db[token]['net']['g']
        model = mrm.MajorityRuleModel(g, {'q': q})
        model.set_initial_status({'model': {'percentage_infected': float(infected)}})

        if 'configuration' in db[token]:
            model.set_initial_status(db[token]['configuration'])

        try:
            r = db[token]
            keys = r['models'].keys()
            if len(keys) > 0:
                mid = len([int(x.split("_")[1]) for x in keys if 'MajorityRule' == x.split("_")[0]])
                r['models']['MajorityRule_%s' % mid] = model
            else:
                r['models']['MajorityRule_0'] = model
            db[token] = r
        except:
            db.close()
            return {'Message': 'Parameter error'}, bad_request

        db.close()
        return {'Message': 'Resource created'}, success


class Sznajd(Resource):

    def put(self):
        """
            @api {put} /api/Sznajd Sznajd
            @ApiDescription Instantiate the Sznajd Model on the network bound to the provided token.
            The model is defined for complete graphs, however it can be applied to generic ones.
            @apiVersion 0.7.0
            @apiParam {String} token    The token.
            @apiParam {Number{0-1}} infected    The initial percentage of infected nodes.
            @apiName sznajd
            @apiGroup Models
            @apiExample [python request] Example usage:
            put('http://localhost:5000/api/Sznajd', data={'token': token, 'infected': percentage})
        """
        token = str(request.form['token'])
        db = shelve.open("data/db/%s" % token)
        if token not in db:
            db.close()
            return {"Message": "Wrong Token"}, bad_request

        infected = request.form['infected']
        if infected == '':
            infected = 0.05

        g = db[token]['net']['g']
        model = sm.SznajdModel(g)
        model.set_initial_status({'model': {'percentage_infected': float(infected)}})

        if 'configuration' in db[token]:
            model.set_initial_status(db[token]['configuration'])

        try:
            r = db[token]
            keys = r['models'].keys()
            if len(keys) > 0:
                mid = len([int(x.split("_")[1]) for x in keys if 'SznajdModel' == x.split("_")[0]])
                r['models']['SznajdModel_%s' % mid] = model
            else:
                r['models']['SznajdModel_0'] = model
            db[token] = r
        except:
            db.close()
            return {'Message': 'Parameter error'}, bad_request

        db.close()
        return {'Message': 'Resource created'}, success

#######################################################################################

class Iterators(Resource):
    """
        @apiDefine Iterators Iterators
                Endpoints belonging to this family allow the user to require
                <a href="#api-Iterators-iterator">step-by-step</a>,  <a href="#api-Iterators-iteratorbunch">partial</a>
                as well as <a href="#api-Iterators-complete">complete</a> runs of the models attached to the experiment.

    """


class Iteration(Resource):

    def post(self):
        """
            @api {post} /api/Iteration Iteration
            @ApiDescription Return the next iteration for all the models bind to the provided token.
            @apiVersion 0.1.0
            @apiName iterator
            @apiGroup Iterators
            @apiParam {String} token    The token.
            @apiParam {String}  models    String composed by comma separated model names.
            @apiSuccess {Object}    iteration  Nodes status after an iteration: 0=susceptible, 1=infected, 2=removed.
            @apiSuccessExample {json} Response example: iteration
           {
                'Model1':
                    {
                        'iteration': 1,
                        'status':
                            {
                                'node0': 1,
                                'node1': 0,
                                'node2': 1,
                                'node3': 0
                            }
                    },
                'Model2':
                    {
                        'iteration': 1,
                        'status':
                            {
                                'node0': 1,
                                'node1': 1,
                                'node2': 0,
                                'node3': 0
                            }
                    }
            }
            @apiExample [python request] Example usage:
                        post('http://localhost:5000/api/Iteration', data={'token': token, 'models': 'model1,model2'})
        """
        token = str(request.form['token'])
        db = shelve.open("data/db/%s" % token)

        if token not in db:
            db.close()
            return {"Message": "Wrong Token"}, bad_request

        ml = []
        if 'models' in request.form:
            ml = request.form['models'].split(',')

        exp = db[token]
        try:

            ml = {c: exp['models'][c] for c in ml if c != ''}
            models = ml if len(ml) > 0 else exp['models']

            results = {}
            for model_name, model in models.iteritems():

                iteration, status = model.iteration()
                del exp['models'][model_name]
                exp['models'][model_name] = model
                db[token] = exp
                results[model_name] = {'iteration': iteration, 'status': status}
        except:
            db.close()
            return {'Message': 'Parameter error'}, bad_request

        db.close()
        return results, success


class IterationBunch(Resource):

    def post(self):
        """
            @api {post} /api/IterationBunch Iteration Bunch
            @ApiDescription Return the next <bunch> iterations for the all the models bind to the provided token.
            @apiVersion 0.1.0
            @apiName iteratorbunch
            @apiGroup Iterators
            @apiParam {String} token    The token.
            @apiParam {String}  models    String composed by comma separated model names.
            @apiParam {Number} bunch    Then number of iteration to return.
            @apiSuccess {Object}    iteration  Nodes status after an iteration: 0=susceptible, 1=infected, 2=removed.
            @apiSuccessExample {json} Response example: iteration
            {
                'Model1':
                    [
                        {
                            'iteration': 1,
                            'status':
                                {
                                    'node0': 1,
                                    'node1': 0,
                                    'node2': 1,
                                    'node3': 0
                                }
                        },
                        {
                            'iteration': 2,
                            'status':
                                {
                                    'node0': 1,
                                    'node1': 1,
                                    'node2': 1,
                                    'node3': 0
                                }
                        }
                    ],
                'Model2':
                    [
                        {
                            'iteration': 1,
                            'status':
                                {
                                    'node0': 1,
                                    'node1': 1,
                                    'node2': 0,
                                    'node3': 0
                                }
                        },
                        {
                            'iteration': 2,
                            'status':
                                {
                                    'node0': 1,
                                    'node1': 1,
                                    'node2': 0,
                                    'node3': 1
                                }
                        }
                    ]
            }

            @apiExample [python request] Example usage:
                        post('http://localhost:5000/api/IterationBunch', data={'token': token, 'bunch': bunch, 'models': 'model1,model2'})
        """
        token = str(request.form['token'])
        db = shelve.open("data/db/%s" % token)

        if token not in db:
            db.close()
            return {"Message": "Wrong Token"},bad_request

        bunch = int(request.form['bunch'])
        results = {}

        exp = db[token]

        ml = []
        if 'models' in request.form:
            ml = request.form['models'].split(',')
        try:
            ml = {c: exp['models'][c] for c in ml if c != ''}
            models = ml if len(ml) > 0 else exp['models']

            for model_name, model in models.iteritems():
                results[model_name] = model.iteration_bunch(bunch)
                del exp['models'][model_name]
                exp['models'][model_name] = model
                db[token] = exp
        except:
            db.close()
            return {'Message': 'Parameter error'}, bad_request

        db.close()
        return results, success


class CompleteRun(Resource):

    def post(self):
        """
            @api {post} /api/CompleteRun Complete Run
            @ApiDescription Return the comlpete run for the all the models bind to the provided token.
            @apiVersion 0.2.0
            @apiName complete
            @apiGroup Iterators
            @apiParam {String} token    The token.
            @apiParam {String}  models    String composed by comma separated model names.
            @apiSuccess {Object}    iteration  Nodes status after an iteration: 0=susceptible, 1=infected, 2=removed.
            @apiSuccessExample {json} Response example: iteration
            {
                'Model1':
                    [
                        {
                            'iteration': 1,
                            'status':
                                {
                                    'node0': 1,
                                    'node1': 0,
                                    'node2': 1,
                                    'node3': 0
                                }
                        },
                        {
                            'iteration': 2,
                            'status':
                                {
                                    'node0': 1,
                                    'node1': 1,
                                    'node2': 1,
                                    'node3': 0
                                }
                        }
                    ],
                'Model2':
                    [
                        {
                            'iteration': 1,
                            'status':
                                {
                                    'node0': 1,
                                    'node1': 1,
                                    'node2': 0,
                                    'node3': 0
                                }
                        },
                        {
                            'iteration': 2,
                            'status':
                                {
                                    'node0': 1,
                                    'node1': 1,
                                    'node2': 0,
                                    'node3': 1
                                }
                        }
                    ]
            }

            @apiExample [python request] Example usage:
                        post('http://localhost:5000/api/CompleteRun', data={'token': token, 'models': 'model1,model2'})
        """
        token = str(request.form['token'])
        db = shelve.open("data/db/%s" % token)

        if token not in db:
            db.close()
            return {"Message": "Wrong Token"}, bad_request

        results = {}

        ml = []
        if 'models' in request.form:
            ml = request.form['models'].split(',')

        exp = db[token]
        try:
            ml = {c: exp['models'][c] for c in ml if c != ''}

            models = ml if len(ml) > 0 else exp['models']

            for model_name, model in models.iteritems():
                results[model_name] = model.complete_run()
                del exp['models'][model_name]
                exp['models'][model_name] = model
                db[token] = exp
        except:
            db.close()
            return {'Message': 'Parameter error'}, bad_request

        db.close()
        return results, success


class Exploratory(Resource):
    """
        @apiDefine Exploratory Exploratory
        An exploratory is a pre-configured experiments. It provides:
            <ul>
                <li>A network topology</li>
                <li>An initial status of nodes and edges attributes</li>
            </ul>
        To setup the exploratory five seps should be followed:
            <ol>
                <li><a href="#api-Experiment-getexp">Create an experiment</a></li>
                <li><a href="#api-Resources-getgraphs">Load</a> a graph resource for which exploratories are available</li>
                <li><a href="#api-loadexploratory">Retrieve</a> the exploratory configuration</li>
                <li><a href="#api-Models">Select</a> one, or more, diffusion model(s)</li>
                <li><a href="#api-Iterators">Execute</a> the simulation</li>
                <li><a href="#api-Experiment-deleteexp">Destroy</a> the experiment. </li>
            </ol>

        """

    def post(self):
        """
            @api {post} /api/Exploratory Get Configuration
            @ApiDescription Load the configuration data for a specific exploratory.
            @apiVersion 0.6.0
            @apiName loadexploratory
            @apiGroup Exploratory
            @apiParam {String} token    The token.
            @apiParam {String} exploratory    The exploratory name.
            @apiExample [python request] Example usage:
                        post('http://localhost:5000/api/Exploratory')
        """
        token = str(request.form['token'])
        db = shelve.open("data/db/%s" % token)

        if token not in db:
            db.close()
            return {"Message": "Wrong Token"}, bad_request

        if "exploratory" in request.form and request.form["exploratory"] != "":
            base_path = "data/exploratories/%s" % request.form["exploratory"]

            try:
                # Read Graph
                net_name = request.form["exploratory"].split("_")[0]

                directed = False
                nets = json.load(open("resources/networks.json"))['networks']
                for net in nets:
                    if net["name"] == net_name:
                        directed = net["directed"]
                        break

                g = None
                if directed:
                    g = nx.DiGraph()
                else:
                    g = nx.Graph()

                f = open("data/networks/%s.csv" % net_name)
                for l in f:
                    l = map(int, l.rstrip().split(","))
                    g.add_edge(l[0], l[1])

                r = db[token]
                r['net'] = {'g': g, 'name': net_name}
                db[token] = r

                # Read Configuration
                conf = {'nodes': {'profile': {}, 'threshold': {}}, 'edges': []}
                f = open("%s/nodes.csv" % base_path)
                for l in f:
                    l = l.rstrip().split(",")
                    conf['nodes']['threshold'][l[0]] = float(l[1])
                    conf['nodes']['profile'][l[0]] = float(l[2])

                f = open("%s/edges.csv" % base_path)
                for l in f:
                    l = l.rstrip().split(",")
                    conf['edges'].append({'source': l[0], 'target': l[1], 'weight': float(l[2])})

                db[token]['configuration'] = conf
                db.close()
                return {'Message': 'Exploratory configuration loaded'}, success

            except:
                db.close()
                return {'Message': 'Parameter error'}, bad_request

    def get(self):
        """
            @api {get} /api/Exploratory  List Exploratories
            @ApiDescription Return the available network endpoints and their parameters
            @apiVersion 0.6.0
            @apiName listexploratory
            @apiGroup Exploratory
            @apiSuccess {Object}    exploratories              List of available exploratories.
            @apiSuccessExample {json} Response example: Available exploratories
                {'exploratory':
                    [
                        {
                            "name": "Lastfm_rock",
                            "network": "Lastfm",
                            "node_attributes": ["profile", "threshold"],
                            "edge_attributes": ["weight"],
                            "description": "Diffusion threshold and profiles computed on rock listening data"
                        }
                    ]
                }
            @apiExample [python request] Example usage:
                        get('http://localhost:5000/api/Exploratory')
        """
        res = json.load(open("resources/exploratories.json"))
        return res, success


api.add_resource(Graph, '/api/GetGraph')
api.add_resource(Generators, '/api/Generators')
api.add_resource(Networks, '/api/Networks')
api.add_resource(ERGraph, '/api/Generators/ERGraph')
api.add_resource(BarabasiAlbertGraph, '/api/Generators/BarabasiAlbertGraph')
api.add_resource(WattsStrogatzGraph, '/api/Generators/WattsStrogatzGraph')
api.add_resource(IndependentCascades, '/api/IndependentCascades')
api.add_resource(Configure, '/api/Configure')
api.add_resource(Models, '/api/Models')
api.add_resource(Threshold, '/api/Threshold')
api.add_resource(SIR, '/api/SIR')
api.add_resource(SI, '/api/SI')
api.add_resource(SIS, '/api/SIS')
api.add_resource(Profile, '/api/Profile')
api.add_resource(ProfileThreshold, '/api/ProfileThreshold')
api.add_resource(Voter, '/api/Voter')
api.add_resource(MaJorityRule, '/api/MajorityRule')
api.add_resource(Sznajd, '/api/Sznajd')
api.add_resource(Experiment, '/api/Experiment')
api.add_resource(ExperimentStatus, '/api/ExperimentStatus')
api.add_resource(Iteration, '/api/Iteration')
api.add_resource(IterationBunch, '/api/IterationBunch')
api.add_resource(CompleteRun, '/api/CompleteRun')
api.add_resource(Exploratory, '/api/Exploratory')

if __name__ == '__main__':
    app.run(debug=True)
