# -*- coding: utf-8 -*-
from flask import Flask, request
import shelve
import dumbdbm
import glob
import os
from utils import generators
from flask_cors import CORS
from flask_restful import Resource, Api
from flask_apidoc import ApiDoc

import ndlib.models.ModelConfig as mc

import ndlib.models.epidemics.ThresholdModel as tm
import ndlib.models.epidemics.SIRModel as sir
import ndlib.models.epidemics.SIModel as si
import ndlib.models.epidemics.SISModel as sis
import ndlib.models.epidemics.SEIRModel as seir
import ndlib.models.epidemics.SEISModel as seis
import ndlib.models.epidemics.ProfileModel as ac
import ndlib.models.epidemics.ProfileThresholdModel as pt
import ndlib.models.epidemics.IndependentCascadesModel as ic
import ndlib.models.epidemics.KerteszThresholdModel as jt

import ndlib.models.opinions.VoterModel as vm
import ndlib.models.opinions.QVoterModel as qvm
import ndlib.models.opinions.MajorityRuleModel as mrm
import ndlib.models.opinions.SznajdModel as sm
import ndlib.models.opinions.CognitiveOpDynModel as cop


import json
import shutil
import networkx as nx
from networkx.readwrite import json_graph
import uuid
import copy
import logging
from logging.handlers import RotatingFileHandler

__author__ = "Giulio Rossetti"
__email__ = "giulio.rossetti@gmail.com"

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 20MB limit for uploads
api = Api(app)
doc = ApiDoc(app=app)
CORS(app)

max_number_of_nodes = 100000
min_number_of_nodes = 200

# Status code
success = 200
created = 201
bad_request = 400
unauthorized = 401
forbidden = 403
not_found = 404
unavailable = 451
not_implemented = 501

# Request Logging
logger = logging.getLogger('werkzeug')
handler = RotatingFileHandler('logs/access.log.gz', maxBytes=1000, backupCount=1, encoding='bz2-codec')
handler.setLevel(logging.INFO)
logger.addHandler(handler)
app.logger.addHandler(handler)


def update_model(md, status):
    config = mc.Configuration()

    # nodes conf
    if 'nodes' in status:
        for cn, cc in status['nodes'].iteritems():
            for n, v in cc.iteritems():
                config.add_node_configuration(cn, int(n), float(v))

    # edges conf
    if 'edges' in status:
        for ce in status['edges']:
            config.add_edge_configuration('threshold', (int(ce['source']), int(ce['target'])), float(ce['weight']))

    # model conf
    for k, v in md.params['model'].iteritems():
        config.add_model_parameter(k, v)

    if 'model' in status:
        for me, mv in status['model'].iteritems():
            config.add_model_parameter(me, float(mv))

    # status conf
    if 'status' in status:
        for se, sv in status['status'].iteritems():
            if se in md.available_statuses:
                config.add_model_initial_configuration(se, map(int, sv))

    md.set_initial_status(config)
    return md


def config_model(token, model_name, model):

    if len(glob.glob("data/db/%s/configuration*" % token)) > 0:
        db_model = load_data("data/db/%s/models" % token)
        r = db_model['models']
        keys = r.keys()

        if len(keys) > 0:
            mid = len([int(x.split("_")[1]) for x in keys if model_name == x.split("_")[0]])
            db_name = '%s_%s' % (model_name, mid)
        else:
            db_name = "%s_0" % model_name

        db_conf = load_data("data/db/%s/configuration" % token)
        mod = update_model(model, db_conf)
        db_model['models'][db_name] = mod
        db_model.close()

    db_model = load_data("data/db/%s/models" % token)
    r = db_model['models']
    keys = r.keys()

    if len(keys) > 0:
        mid = len([int(x.split("_")[1]) for x in keys if model_name == x.split("_")[0]])
        db_name = '%s_%s' % (model_name, mid)
    else:
        db_name = "%s_0" % model_name
    r[db_name] = {}
    db_model['models'] = r
    db_model.close()

    db_md_conf = load_data("data/db/%s/%s" % (token, db_name))
    r = db_md_conf
    r[db_name] = model
    db_md_conf = r
    db_md_conf.close()


def load_data(path):
    db = dumbdbm.open(path)
    db_net = shelve.Shelf(db)
    return db_net


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
        directory = "data/db/%s" % token
        if not os.path.exists(directory):
            os.makedirs(directory)

        db_net = load_data("%s/net" % directory)
        db_models = load_data("%s/models" % directory)

        r = db_models
        r['models'] = {}
        db_models = r
        db_net.close()
        db_models.close()

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
            shutil.rmtree("data/db/%s" % token)
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
        if not os.path.exists("data/db/%s" % token):
            return {"Message": "Wrong Token"}, bad_request

        result = {}
        db_net = load_data("data/db/%s/net" % token)

        try:
            exp = db_net
            net_info = {k: v for k, v in exp['net'].iteritems() if k != 'g'}
            result['Network'] = net_info
            db_net.close()
        except:
            return {'Message': 'No resources attached to this token'}, not_found
        try:
            db_model = load_data("data/db/%s/models" % token)
            exp = db_model['models']
            model_names = exp.keys()
            db_model.close()

            models = {}
            for model in model_names:
                db_model = load_data("data/db/%s/%s" % (token, model))
                exp = db_model
                models[model] = exp[model].get_info()
                db_model.close()
            result['Models'] = models
            return result
        except:
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
        if not os.path.exists("data/db/%s" % token):
            return {"Message": "Wrong Token"}, bad_request

        ml = []
        if 'models' in request.form:
            ml = request.form['models'].split(',')

        db_models = load_data("data/db/%s/models" % token)

        exp = db_models['models'].keys()
        db_models.close()
        try:
            ml = [c for c in ml if c != '']
            models = ml if len(ml) > 0 else exp

            for model_name in models:

                db_mod = load_data("data/db/%s/%s" % (token, model_name))
                r = db_mod
                md = copy.deepcopy(r[model_name])
                md.reset()
                md.reset()
                db_mod[model_name] = md
                db_mod.close()
        except:
            return {'Message': 'Parameter error'}, bad_request
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

        if not os.path.exists("data/db/%s" % token):
            return {"Message": "Wrong Token"}, bad_request

        db_net = load_data("data/db/%s/net" % token)

        try:
            # res = json.load(open("resources/networks.json"))['networks']
            # available = True
            # for net in res:
            #     if net['name'] == db_net['net']['name']:
            #         available = net['open_access']
            #         break

            # if available:
            g = db_net['net']['g']
            res = json_graph.node_link_data(g)
            #else:
            #    db_net.close()
            #    return {"Message": "Dataset in read-only access."}, unavailable
        except:
            db_net.close()
            return {"Message": "No graph resource assigned to the experiment"}, not_found

        db_net.close()
        return res, success


class Resources(Resource):
    """
        @apiDefine Resources Resources
                Endpoints belonging to this family provide access to resources, networks and models, listing and lookup
                facilities.</br>
                They also handle the destruction phase of experiment resources.
    """


class UploadNetwork(Resource):

    def put(self):
        """
            @api {put} /api/UploadNetwork Upload Network
            @ApiDescription
            @apiVersion 0.9.0
            @apiParam {String}  token   The token.
            @apiParam {Boolean} directed If the graph is directed
            @apiParam {json} graph JSON description of the graph attributes.
            @apiParamExample {json} graph example:
                {
                "directed": false,
                "graph": {
                    "name": "graph_name"
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
            @apiName upload
            @apiGroup Networks
            @apiExample [python request] Example usage:
            put('http://localhost:5000/api/UploadNetwork', data={'file': JSON, 'directed': False, 'token': token})
        """
        token = str(request.form['token'])

        if not os.path.exists("data/db/%s" % token):
            return {"Message": "Wrong Token"}, bad_request

        try:
            data = json.loads(request.form['file'])
        except:
            return {"Message": "Value Error: No JSON object could be decoded"}, bad_request

        try:
            g = None
            if 'directed' in request.form:
                directed = bool(request.form['directed'])
            if directed:
                g = json_graph.node_link_graph(data, directed=True)
            else:
                g = json_graph.node_link_graph(data, directed=False)

            if len(g.nodes()) < min_number_of_nodes or len(g.nodes()) > max_number_of_nodes:
                return {"Message": "Node number out fo range."}, bad_request

            db_net = load_data("data/db/%s/net" % token)
            r = db_net
            r['net'] = {'g': g, 'name': 'Uploaded Graph'}
            db_net = r
            db_net.close()
        except:
            return {'Message': 'Parameter error'}, bad_request

        return {"Message": "Configuration applied"}, success


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

        if not os.path.exists("data/db/%s" % token):
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
                g.add_edge(int(l[0]), int(l[1]))

            db_net = load_data("data/db/%s/net" % token)
            r = db_net
            r['net'] = {'g': g, 'name': name}
            db_net = r
            db_net.close()
            return {'Message': 'Network correctly loaded'}, success
        except:
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

        if not os.path.exists("data/db/%s" % token):
            return {"Message": "Wrong Token"}, bad_request

        db_net = load_data("data/db/%s/net" % token)
        r = db_net

        del r['net']
        r['net'] = {}
        db_net = r
        db_net.close()
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

        if not os.path.exists("data/db/%s" % token):
            return {"Message": "Wrong Token"}, bad_request

        n = int(request.form['n'])
        if n < min_number_of_nodes or n > max_number_of_nodes:
            return {"Message": "Node number out fo range."}, bad_request

        db_net = load_data("data/db/%s/net" % token)

        try:
            p = float(request.form['p'])
            directed = False
            if 'directed' in request.form:
                directed = bool(request.form['directed'])

            g = nx.erdos_renyi_graph(n, p, directed)

            r = db_net
            r['net'] = {'g': g, 'name': 'ERGraph', 'params': {'n': n, 'p': p}}
            db_net = r
        except:
            db_net.close()
            return {'Message': 'Parameter error'}, bad_request

        db_net.close()
        return {'Message': 'Resource created'}, success


class PlantedPartition(Resource):

    def put(self):
        """
            @api {put} /api/Generators/PlantedPartition Planted l-partitions
            @ApiDescription Create a Planted l-Parition graph compliant to the specified parameters and bind it to the provided token
            @apiVersion 0.9.2
            @apiParam {String} token    The token.
            @apiParam {Number} l    The number of groups.
            @apiParam {Number} k    The number of nodes per group.
            @apiParam {Number} pin  The probability of connecting vertices within a group.
            @apiParam {Number} pout    The probability of connecting vertices between a group.
            @apiParam {Boolean} directed    If the graph should be directed.
             If not specified an undirected graph will be generated.
            @apiName PlantedPartition
            @apiGroup Networks
            @apiExample [python request] Example usage:
            put('http://localhost:5000/api/Generators/PlantedPartition', data={'l': l, 'k': k, 'pin': pin, 'pout': pout, 'token': token})
        """
        token = str(request.form['token'])

        if not os.path.exists("data/db/%s" % token):
            return {"Message": "Wrong Token"}, bad_request

        k = int(request.form['k'])
        l = int(request.form['l'])
        if k*l < min_number_of_nodes or k*l > max_number_of_nodes:
            return {"Message": "Node number out fo range."}, bad_request

        db_net = load_data("data/db/%s/net" % token)

        try:
            pin = float(request.form['pin'])
            pout = float(request.form['pout'])

            directed = False
            if 'directed' in request.form:
                directed = bool(request.form['directed'])

            g = generators.planted_partition_graph(l, k, pin, pout, directed=directed)

            r = db_net
            r['net'] = {'g': g, 'name': 'PlantedPartition', 'params': {'l': l, 'k': k, 'pin': pin, 'pout': pout}}
            db_net = r
        except:
            db_net.close()
            return {'Message': 'Parameter error'}, bad_request

        db_net.close()
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

        if not os.path.exists("data/db/%s" % token):
            return {"Message": "Wrong Token"}, bad_request

        n = int(request.form['n'])
        if n < min_number_of_nodes or n > max_number_of_nodes:
            return {"Message": "Node number out fo range."}, bad_request

        db_net = load_data("data/db/%s/net" % token)

        try:
            m = int(request.form['m'])
            g = nx.barabasi_albert_graph(n, m)

            r = db_net
            r['net'] = {'g': g, 'name': 'BAGraph', 'params': {'n': n, 'm': m}}
            db_net = r
        except:
            db_net.close()
            return {'Message': 'Parameter error'}, bad_request

        db_net.close()
        return {'Message': 'Resource created'}, success


class ClusteredBarabasiAlbertGraph(Resource):

    def put(self):
        """
            @api {put} /api/Generators/ClusteredBarabasiAlbertGraph Clustered-Barabasi-Albert
            @ApiDescription Create a CBA graph compliant to the specified parameters and bind it to the provided token
            @apiVersion 0.9.2
            @apiParam {String} token    The token.
            @apiParam {Number{200..100000}} n    The number of nodes.
            @apiParam {Number{1..}} m    The number of edges attached to each new node.
            @apiParam {Number{0-1}} p   Probability of adding a triangle after adding a random edge
            @apiName CBAGraph
            @apiGroup Networks
            @apiExample [python request] Example usage:
            put('http://localhost:5000/api/Generators/ClusteredBarabasiAlbertGraph', data={'n': n, 'm': m, 'token': token})
        """
        token = str(request.form['token'])

        if not os.path.exists("data/db/%s" % token):
            return {"Message": "Wrong Token"}, bad_request

        n = int(request.form['n'])
        if n < min_number_of_nodes or n > max_number_of_nodes:
            return {"Message": "Node number out fo range."}, bad_request

        db_net = load_data("data/db/%s/net" % token)

        try:
            m = int(request.form['m'])
            p = float(request.form['p'])
            g = nx.powerlaw_cluster_graph(n, m, p)

            r = db_net
            r['net'] = {'g': g, 'name': 'CBAGraph', 'params': {'n': n, 'm': m, 'p': p}}
            db_net = r
        except:
            db_net.close()
            return {'Message': 'Parameter error'}, bad_request

        db_net.close()
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

        if not os.path.exists("data/db/%s" % token):
            return {"Message": "Wrong Token"}, bad_request

        n = int(request.form['n'])
        if n < min_number_of_nodes or n > max_number_of_nodes:
            return {"Message": "Node number out fo range."}, bad_request

        db_net = load_data("data/db/%s/net" % token)

        try:
            k = int(request.form['k'])
            p = float(request.form['p'])
            g = nx.watts_strogatz_graph(n, k, p)
            r = db_net
            r['net'] = {'g': g, 'name': 'WSGraph', 'params': {'n': n, 'k': k, 'p': p}}
            db_net = r
        except:
            db_net.close()
            return {'Message': 'Parameter error'}, bad_request

        db_net.close()
        return {'Message': 'Resource created'}, success


class CompleteGraph(Resource):

    def put(self):
        """
            @api {put} /api/Generators/CompleteGraph Complete Graph
            @ApiDescription Create a complete graph of size n and bind it to the provided token
            @apiVersion 0.9.0
            @apiParam {String} token    The token.
            @apiParam {Number} n    The number of nodes.
            @apiName CompleteGraph
            @apiGroup Networks
            @apiExample [python request] Example usage:
            put('http://localhost:5000/api/Generators/CompleteGraph', data={'n': n, 'token': token})
        """
        token = str(request.form['token'])

        if not os.path.exists("data/db/%s" % token):
            return {"Message": "Wrong Token"}, bad_request

        n = int(request.form['n'])
        if n < 100 or n > max_number_of_nodes:
            return {"Message": "Node number out fo range."}, bad_request

        db_net = load_data("data/db/%s/net" % token)

        try:
            n = int(request.form['n'])
            g = nx.complete_graph(n)
            r = db_net
            r['net'] = {'g': g, 'name': 'CompleteGraph', 'params': {'n': n}}
            db_net = r
        except:
            db_net.close()
            return {'Message': 'Parameter error'}, bad_request

        db_net.close()
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

        if not os.path.exists("data/db/%s" % token):
            return {"Message": "Wrong Token"}, bad_request

        try:
            ml = []
            if 'models' in request.form:
                ml = request.form['models'].split(',')

            db_models = load_data("data/db/%s/models" % token)

            exp = db_models['models'].keys()
            db_models['models'] = {}
            db_models.close()

            ml = [c for c in ml if c != '']
            models = ml if len(ml) > 0 else exp

            for model_name in models:
                map(os.remove, glob.glob("data/db/%s/%s*" % (token, model_name)))

        except:
            return {'Message': 'Parameter error'}, bad_request

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
                    'model': {'model_parameter': parameter_value},
                    'status': {'status_name': [node1, node2, node3]}
                }
            @apiName configure
            @apiGroup Experiment
            @apiExample [python request] Example usage:
            put('http://localhost:5000/api/Configure', data={'status': json, 'models': 'model1,model2','token': token})
        """
        token = str(request.form['token'])

        if not os.path.exists("data/db/%s" % token):
            return {"Message": "Wrong Token"}, bad_request

        try:
            status = json.loads(request.form['status'])
        except:
            return {"Message": "Value Error: No JSON object could be decoded"}, bad_request

        db_models = load_data("data/db/%s/models" % token)

        exp = db_models['models'].keys()
        db_models.close()

        try:
            ml = []
            if 'models' in request.form:
                ml = request.form['models'].split(',')

            ml = [c for c in ml if c != '']
            models = ml if len(ml) > 0 else exp

            for model_name in models:
                db_mod = load_data("data/db/%s/%s" % (token, model_name))
                r = db_mod
                md = copy.deepcopy(r[model_name])
                md = update_model(md, status)
                db_mod[model_name] = md
                db_mod.close()
        except:
            return {'Message': "Parameter error"}, bad_request

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
            put('http://localhost:5000/api/Threshold', data={'token': token, 'infected': percentage, 'threshold': threshold})
        """
        token = str(request.form['token'])

        if not os.path.exists("data/db/%s" % token):
            return {"Message": "Wrong Token"}, bad_request

        infected = 0.05
        if 'infected' in request.form and request.form['infected'] != "":
            infected = request.form['infected']

        threshold = 0
        if 'threshold' in request.form and request.form['threshold'] != "":
            threshold = request.form['threshold']

        db_net = load_data("data/db/%s/net" % token)

        g = db_net['net']['g']
        db_net.close()

        model = tm.ThresholdModel(g)
        config = mc.Configuration()
        config.add_model_parameter('percentage_infected', float(infected))

        if float(threshold) > 0:
            for n in g.nodes():
                config.add_node_configuration("threshold", n, float(threshold))
        model.set_initial_status(config)

        try:
            config_model(token, "Threshold", model)
        except:
            return {'Message': 'Parameter error'}, bad_request

        return {'Message': 'Resource created'}, success


class IndependentCascades(Resource):

    def put(self):
        """
            @api {put} /api/IndependentCascades Independent Cascades
            @ApiDescription Instantiate an Independent Cascades Model on the network bound to the provided token.
                The edge threshold is assumed equal to 0.1 divided for all edges:
                this behavior can be changed by using the <a href="#api-Experiment-configure"> advanced configuration </a> endpoint.
            @apiVersion 0.5.0
            @apiParam {String} token    The token.
            @apiParam {Number{0-1}} infected    The initial percentage of infected nodes.
            @apiName indepcascades
            @apiGroup Models
            @apiExample [python request] Example usage:
            put('http://localhost:5000/api/IndependentCascades', data={'token': token, 'infected': percentage})
        """
        token = str(request.form['token'])

        if not os.path.exists("data/db/%s" % token):
            return {"Message": "Wrong Token"}, bad_request

        infected = 0.05
        if 'infected' in request.form and request.form['infected'] != "":
            infected = request.form['infected']

        db_net = load_data("data/db/%s/net" % token)

        g = db_net['net']['g']
        db_net.close()

        model = ic.IndependentCascadesModel(g)
        config = mc.Configuration()
        config.add_model_parameter('percentage_infected', float(infected))

        threshold = 0.1
        for e in g.edges():
            config.add_edge_configuration("threshold", e, threshold)

        model.set_initial_status(config)

        try:
            config_model(token, "IndependentCascades", model)
        except:
            return {'Message': 'Parameter error'}, bad_request

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

        if not os.path.exists("data/db/%s" % token):
            return {"Message": "Wrong Token"}, bad_request

        try:
            beta = request.form['beta']
            gamma = request.form['gamma']
            infected = request.form['infected']
            if infected == '':
                infected = 0.05

            db_net = load_data("data/db/%s/net" % token)

            g = db_net['net']['g']
            db_net.close()

            model = sir.SIRModel(g)
            config = mc.Configuration()
            config.add_model_parameter('percentage_infected', float(infected))
            config.add_model_parameter('beta', float(beta))
            config.add_model_parameter('gamma', float(gamma))
            model.set_initial_status(config)

            config_model(token, "SIR", model)
        except:
            return {'Message': 'Parameter error'}, bad_request

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

        if not os.path.exists("data/db/%s" % token):
            return {"Message": "Wrong Token"}, bad_request

        try:
            beta = request.form['beta']
            infected = request.form['infected']
            if infected == '':
                infected = 0.05

            db_net = load_data("data/db/%s/net" % token)

            g = db_net['net']['g']
            db_net.close()

            model = si.SIModel(g)
            config = mc.Configuration()
            config.add_model_parameter('percentage_infected', float(infected))
            config.add_model_parameter('beta', float(beta))
            model.set_initial_status(config)

            config_model(token, "SI", model)
        except:
            return {'Message': 'Parameter error'}, bad_request

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

        if not os.path.exists("data/db/%s" % token):
            return {"Message": "Wrong Token"}, bad_request

        try:
            beta = request.form['beta']
            lamb = request.form['lambda']
            infected = request.form['infected']
            if infected == '':
                infected = 0.05

            db_net = load_data("data/db/%s/net" % token)

            g = db_net['net']['g']
            db_net.close()

            model = sis.SISModel(g)
            config = mc.Configuration()
            config.add_model_parameter('percentage_infected', float(infected))
            config.add_model_parameter('beta', float(beta))
            config.add_model_parameter('lambda', float(lamb))
            model.set_initial_status(config)

            config_model(token, "SIS", model)
        except:
            return {'Message': 'Parameter error'}, bad_request

        return {'Message': 'Resource created'}, success


class SEIS(Resource):

    def put(self):
        """
            @api {put} /api/SEIS SEIS
            @ApiDescription Instantiate a SEIS Model on the network bound to the provided token.
            @apiVersion 1.0.0
            @apiParam {String} token    The token.
            @apiParam {Number{0-1}} infected    The initial percentage of infected nodes.
            @apiParam {Number{0-1}}  beta    Infection rate.
            @apiParam {Number{0-1}}  lambda    Recovery rate.
            @apiParam {Number{0-1}}  alpha   Incubation period.
            @apiName seis
            @apiGroup Models
            @apiExample [python request] Example usage:
            put('http://localhost:5000/api/SEIS', data={'beta': beta, 'lambda': lambda, 'alpha': alpha, 'infected': percentage, 'token': token})
        """
        token = str(request.form['token'])

        if not os.path.exists("data/db/%s" % token):
            return {"Message": "Wrong Token"}, bad_request

        try:
            beta = request.form['beta']
            lamb = request.form['lambda']
            alpha = request.form['alpha']
            infected = request.form['infected']
            if infected == '':
                infected = 0.05

            db_net = load_data("data/db/%s/net" % token)

            g = db_net['net']['g']
            db_net.close()

            model = seis.SEISModel(g)
            config = mc.Configuration()
            config.add_model_parameter('percentage_infected', float(infected))
            config.add_model_parameter('beta', float(beta))
            config.add_model_parameter('lambda', float(lamb))
            config.add_model_parameter('alpha', float(alpha))
            model.set_initial_status(config)

            config_model(token, "SEIS", model)
        except:
            return {'Message': 'Parameter error'}, bad_request

        return {'Message': 'Resource created'}, success


class SEIR(Resource):

    def put(self):
        """
            @api {put} /api/SEIR SEIR
            @ApiDescription Instantiate a SEIR Model on the network bound to the provided token.
            @apiVersion 1.0.0
            @apiParam {String} token    The token.
            @apiParam {Number{0-1}} infected    The initial percentage of infected nodes.
            @apiParam {Number{0-1}}  beta    Infection rate.
            @apiParam {Number{0-1}}  gamma    Recovery rate.
            @apiParam {Number{0-1}}  alpha   Incubation period.
            @apiName seir
            @apiGroup Models
            @apiExample [python request] Example usage:
            put('http://localhost:5000/api/SEIS', data={'beta': beta, 'gamma': gamma, 'alpha': alpha, 'infected': percentage, 'token': token})
        """
        token = str(request.form['token'])

        if not os.path.exists("data/db/%s" % token):
            return {"Message": "Wrong Token"}, bad_request

        try:
            beta = request.form['beta']
            gamma = request.form['gamma']
            alpha = request.form['alpha']
            infected = request.form['infected']
            if infected == '':
                infected = 0.05

            db_net = load_data("data/db/%s/net" % token)

            g = db_net['net']['g']
            db_net.close()

            model = seir.SEIRModel(g)
            config = mc.Configuration()
            config.add_model_parameter('percentage_infected', float(infected))
            config.add_model_parameter('beta', float(beta))
            config.add_model_parameter('gamma', float(gamma))
            config.add_model_parameter('alpha', float(alpha))
            model.set_initial_status(config)

            config_model(token, "SEIR", model)
        except:
            return {'Message': 'Parameter error'}, bad_request

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
            @apiParam {Number{0-1}} blocked   Probability for a node that chose to not adopt to became blocked
            @apiParam {Number{0-1}} adopter_rate    Probability of spontaneous adoption
            @apiParam {Number{0-1}} infected    The initial percentage of infected nodes.
            @apiName profile
            @apiGroup Models
            @apiExample [python request] Example usage:
            put('http://localhost:5000/api/Profile', data={'token': token, 'infected': percentage})
        """
        token = str(request.form['token'])

        if not os.path.exists("data/db/%s" % token):
            return {"Message": "Wrong Token"}, bad_request

        profile = 0
        if 'profile' in request.form and request.form['profile'] != "":
            profile = float(request.form['profile'])

        try:
            infected = request.form['infected']
            if infected == '':
                infected = 0.05

            db_net = load_data("data/db/%s/net" % token)

            g = db_net['net']['g']
            db_net.close()

            model = ac.ProfileModel(g)

            config = mc.Configuration()
            config.add_model_parameter('percentage_infected', float(infected))

            if float(profile) > 0:
                for n in g.nodes():
                    config.add_node_configuration("profile", n, float(profile))

            blocked = 0
            if 'blocked' in request.form and request.form['blocked'] != "":
                blocked = float(request.form['blocked'])

            config.add_model_parameter('blocked', float(blocked))

            adopter_rate = 0
            if 'adopter_rate' in request.form and request.form['adopter_rate'] != "":
                adopter_rate = float(request.form['adopter_rate'])

            config.add_model_parameter('adopter_rate', float(adopter_rate))
            model.set_initial_status(config)

            config_model(token, "Profile", model)
        except:
            return {'Message': 'Parameter error'}, bad_request

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
            @apiParam {Number{0-1}} blocked   Probability for a node that chose to not adopt to became blocked
            @apiParam {Number{0-1}} adopter_rate    Probability of spontaneous adoption
            @apiParam {Number{0-1}} infected    The initial percentage of infected nodes.
            @apiName profilethreshold
            @apiGroup Models
            @apiExample [python request] Example usage:
            put('http://localhost:5000/api/ProfileThreshold', data={'token': token, 'infected': percentage, 'threshold': threshold, 'profile': profile})
        """
        token = str(request.form['token'])

        if not os.path.exists("data/db/%s" % token):
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

            db_net = load_data("data/db/%s/net" % token)

            g = db_net['net']['g']
            db_net.close()

            model = pt.ProfileThresholdModel(g)
            config = mc.Configuration()
            config.add_model_parameter('percentage_infected', float(infected))

            if float(profile) > 0:
                for n in g.nodes():
                    config.add_node_configuration("profile", n, float(profile))

            if float(threshold) > 0:
                for n in g.nodes():
                    config.add_node_configuration("threshold", n, float(profile))

            blocked = 0
            if 'blocked' in request.form and request.form['blocked'] != "":
                blocked = float(request.form['blocked'])

            config.add_model_parameter('blocked', float(blocked))

            adopter_rate = 0
            if 'adopter_rate' in request.form and request.form['adopter_rate'] != "":
                adopter_rate = float(request.form['adopter_rate'])

            config.add_model_parameter('adopter_rate', float(adopter_rate))
            model.set_initial_status(config)

            config_model(token, "ProfileThreshold", model)
        except:
            return {'Message': 'Parameter error'}, bad_request

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

        if not os.path.exists("data/db/%s" % token):
            return {"Message": "Wrong Token"}, bad_request

        infected = request.form['infected']
        if infected == '':
            infected = 0.05

        db_net = load_data("data/db/%s/net" % token)

        g = db_net['net']['g']
        db_net.close()

        model = vm.VoterModel(g)
        config = mc.Configuration()
        config.add_model_parameter('percentage_infected', float(infected))
        model.set_initial_status(config)

        try:
            config_model(token, "Voter", model)
        except:
            return {'Message': 'Parameter error'}, bad_request

        return {'Message': 'Resource created'}, success


class QVoter(Resource):

    def put(self):
        """
            @api {put} /api/QVoter QVoter
            @ApiDescription Instantiate the QVoter Model on the network bound to the provided token.
            @apiVersion 0.9.0
            @apiParam {String} token    The token.
            @apiParam {Number{0-1}} infected    The initial percentage of infected nodes.
            @apiParam {Number} q Number of neighbours that affect the opinion of an agent
            @apiName qvoter
            @apiGroup Models
            @apiExample [python request] Example usage:
            put('http://localhost:5000/api/QVoter', data={'token': token, 'q': number,'infected': percentage})
        """
        token = str(request.form['token'])

        if not os.path.exists("data/db/%s" % token):
            return {"Message": "Wrong Token"}, bad_request

        try:
            infected = request.form['infected']
            if infected == '':
                infected = 0.05
            q = int(request.form['q'])

            db_net = load_data("data/db/%s/net" % token)

            g = db_net['net']['g']
            db_net.close()

            model = qvm.QVoterModel(g)
            config = mc.Configuration()
            config.add_model_parameter("q", q)
            config.add_model_parameter('percentage_infected', float(infected))
            model.set_initial_status(config)

            config_model(token, "QVoterModel", model)
        except:
            return {'Message': 'Parameter error'}, bad_request

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

        if not os.path.exists("data/db/%s" % token):
            return {"Message": "Wrong Token"}, bad_request

        try:
            infected = request.form['infected']
            if infected == '':
                infected = 0.05
            q = int(request.form['q'])

            db_net = load_data("data/db/%s/net" % token)

            g = db_net['net']['g']
            db_net.close()

            model = mrm.MajorityRuleModel(g)
            config = mc.Configuration()
            config.add_model_parameter("q", q)
            config.add_model_parameter('percentage_infected', float(infected))
            model.set_initial_status(config)

            config_model(token, "MajorityRule", model)
        except:
            return {'Message': 'Parameter error'}, bad_request

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

        if not os.path.exists("data/db/%s" % token):
            return {"Message": "Wrong Token"}, bad_request

        try:
            infected = request.form['infected']
            if infected == '':
                infected = 0.05

            db_net = load_data("data/db/%s/net" % token)

            g = db_net['net']['g']
            db_net.close()

            model = sm.SznajdModel(g)

            config = mc.Configuration()
            config.add_model_parameter('percentage_infected', float(infected))
            model.set_initial_status(config)

            config_model(token, "Sznajd", model)
        except:
            return {'Message': 'Parameter error'}, bad_request

        return {'Message': 'Resource created'}, success


class KerteszThreshold(Resource):

    def put(self):
        """
            @api {put} /api/KerteszThreshold    KerteszThreshold
            @ApiDescription Instantiate a KerteszThreshold Model on the network bound to the provided token.
            @apiVersion 0.9.1
            @apiParam {String} token    The token.
            @apiParam {Number{0-1}} threshold    A fixed threshold value for all the nodes: if not specified the
                                                thresholds will be assigned using a normal distribution.
            @apiParam {Number{0-1}} infected    The initial percentage of infected nodes.
            @apiParam {Number {0-1}} adopter_rate    The adopter rate. Fixed probability of self-infection per iteration.
            @apiParam {Number {0-1}} blocked    Percentage of blocked nodes.
            @apiName KerteszThreshold
            @apiGroup Models
            @apiExample [python request] Example usage:
            put('http://localhost:5000/api/KerteszThreshold', data={'token': token, 'infected': percentage, 'adopters_rate': adopters_rate, 'blocked': blocked, 'threshold': threshold})
        """
        token = str(request.form['token'])

        if not os.path.exists("data/db/%s" % token):
            return {"Message": "Wrong Token"}, bad_request

        infected = 0.05
        if 'infected' in request.form and request.form['infected'] != "":
            infected = float(request.form['infected'])

        threshold = 0
        if 'threshold' in request.form and request.form['threshold'] != "":
            threshold = float(request.form['threshold'])

        adopter_rate = 0.1
        if 'adopter_rate' in request.form and request.form['adopter_rate'] != "":
            adopter_rate = float(request.form['adopter_rate'])

        blocked = 0.1
        if 'blocked' in request.form and request.form['blocked'] != "":
            blocked = float(request.form['blocked'])

        db_net = load_data("data/db/%s/net" % token)

        g = db_net['net']['g']
        db_net.close()

        model = jt.KerteszThresholdModel(g)
        config = mc.Configuration()
        config.add_model_parameter('percentage_infected', infected)
        config.add_model_parameter('adopter_rate', adopter_rate)
        config.add_model_parameter('percentage_blocked', blocked)

        if float(threshold) > 0:
            for n in g.nodes():
                config.add_node_configuration("threshold", n, float(threshold))

        model.set_initial_status(config)

        try:
            config_model(token, "KerteszThreshold", model)
        except:
            return {'Message': 'Parameter error'}, bad_request

        return {'Message': 'Resource created'}, success


class CognitiveOpinionDynamic(Resource):

    def put(self):
        """
            @api {put} /api/CognitiveOpinionDynamic    CognitiveOpinionDynamic
            @ApiDescription Instantiate a CognitiveOpinionDynamic Model on the network bound to the provided token.
            @apiVersion 0.9.1
            @apiParam {String} token    The token.
            @apiParam {Number{0-1}} I    External information.
            @apiParam {Number{0-1}} T_range_min Minimum of the range of initial values for node parameter T.
            @apiParam {Number{0-1}} T_range_max Maximum of the range of initial values for node parameter T. If T_range_min>T_range_max they are swapped;
            @apiParam {Number{0-1}} B_range_min Minimum of the range of initial values for node parameter B;
            @apiParam {Number{0-1}} B_range_max Maximum of the range of initial values for node parameter B. If B_range_min>B_range_max they are swapped;
            @apiParam {Number{0-1}} R_fraction_negative Fraction of individuals having the node parameter R=-1;
            @apiParam {Number{0-1}} R_fraction_neutral  Fraction of individuals having the node parameter R=0;
            @apiParam {Number{0-1}} R_fraction_positive Fraction of individuals having the node parameter R=1. The following relation should hold: R_fraction_negative+R_fraction_neutral+R_fraction_positive=1. To achieve this, the fractions selected will be normalised to sum 1.



            @apiName CognitiveOpinionDynamic
            @apiGroup Models
            @apiExample [python request] Example usage:
            put('http://localhost:5000/api/CognitiveOpinionDynamic', data={'token': token, 'infected': percentage, 'adopters_rate': adopters_rate, 'blocked': blocked, 'threshold': threshold})
        """
        token = str(request.form['token'])

        if not os.path.exists("data/db/%s" % token):
            return {"Message": "Wrong Token"}, bad_request

        I = 0.15
        T_range_min, T_range_max = 0, 1
        B_range_min, B_range_max = 0, 1
        R_fraction_negative, R_fraction_neutral, R_fraction_positive = 1/3.0, 1/3.0, 1/3.0

        if 'I' in request.form and request.form['I'] != "":
            I = float(request.form['I'])

        if 'T_range_min' in request.form and request.form['T_range_min'] != "":
            T_range_min = float(request.form['T_range_min'])

        if 'T_range_max' in request.form and request.form['T_range_max'] != "":
            T_range_max = float(request.form['T_range_max'])

        if 'B_range_min' in request.form and request.form['B_range_min'] != "":
            B_range_min = float(request.form['B_range_min'])

        if 'B_range_max' in request.form and request.form['B_range_max'] != "":
            B_range_max = float(request.form['B_range_max'])

        if 'R_fraction_negative' in request.form and request.form['R_fraction_negative'] != "":
            R_fraction_negative = float(request.form['R_fraction_negative'])

        if 'R_fraction_neutral' in request.form and request.form['R_fraction_neutral'] != "":
            R_fraction_neutral = float(request.form['R_fraction_neutral'])

        if 'R_fraction_positive' in request.form and request.form['R_fraction_positive'] != "":
            R_fraction_positive = float(request.form['R_fraction_positive'])

        db_net = load_data("data/db/%s/net" % token)

        g = db_net['net']['g']
        db_net.close()

        model = cop.CognitiveOpDynModel(g)

        config = mc.Configuration()
        config.add_model_parameter("I", I)
        config.add_model_parameter("B_range_min", B_range_min)
        config.add_model_parameter("B_range_max", B_range_max)
        config.add_model_parameter("T_range_min", T_range_min)
        config.add_model_parameter("T_range_max", T_range_max)
        config.add_model_parameter("R_fraction_negative", R_fraction_negative)
        config.add_model_parameter("R_fraction_neutral", R_fraction_neutral)
        config.add_model_parameter("R_fraction_positive", R_fraction_positive)
        config.add_model_parameter('percentage_infected', 0.1)
        model.set_initial_status(config)

        try:
            config_model(token, "CognitiveOpinionDynamic", model)
        except:
            return {'Message': 'Parameter error'}, bad_request

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

        if not os.path.exists("data/db/%s" % token):
            return {"Message": "Wrong Token"}, bad_request

        ml = []
        if 'models' in request.form:
            ml = request.form['models'].split(',')

        db_models = load_data("data/db/%s/models" % token)

        exp = db_models['models'].keys()
        db_models.close()
        try:

            ml = [c for c in ml if c != '']
            models = ml if len(ml) > 0 else exp

            results = {}
            for model_name in models:

                db_mod = load_data("data/db/%s/%s" % (token, model_name))
                r = db_mod
                md = copy.deepcopy(r[model_name])
                db_mod.close()
                map(os.remove, glob.glob("data/db/%s/%s*" % (token, model_name)))
                its = md.iteration(node_status=True)

                db_mod = load_data("data/db/%s/%s" % (token, model_name))
                db_mod[model_name] = md
                db_mod.close()

                results[model_name] = {'iteration': its['iteration'], 'status': its['status']}
        except:
           return {'Message': 'Parameter error'}, bad_request

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

        if not os.path.exists("data/db/%s" % token):
            return {"Message": "Wrong Token"}, bad_request

        bunch = int(request.form['bunch'])

        ml = []
        if 'models' in request.form:
            ml = request.form['models'].split(',')

        db_models = load_data("data/db/%s/models" % token)

        exp = db_models['models'].keys()

        db_models.close()
        try:
            ml = [c for c in ml if c != '']
            models = ml if len(ml) > 0 else exp

            results = {}
            for model_name in models:
                db_mod = load_data("data/db/%s/%s" % (token, model_name))

                r = db_mod
                md = copy.deepcopy(r[model_name])
                db_mod.close()

                map(os.remove, glob.glob("data/db/%s/%s*" % (token, model_name)))
                results[model_name] = md.iteration_bunch(bunch)

                db_mod = load_data("data/db/%s/%s" % (token, model_name))
                db_mod[model_name] = md
                db_mod.close()
        except:
           return {'Message': 'Parameter error'}, bad_request

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
            @api {post} /api/Exploratory Load Exploratory
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

        if not os.path.exists("data/db/%s" % token):
            return {"Message": "Wrong Token"}, bad_request

        if "exploratory" in request.form and request.form["exploratory"] != "":
            base_path = "data/exploratories/%s" % request.form["exploratory"]

            try:
                # Read Graph
                net_name = request.form["exploratory"].split("_")[0]

                directed = False

                g = None
                if directed:
                    g = nx.DiGraph()
                else:
                    g = nx.Graph()

                f = open("data/networks/%s.csv" % net_name)
                for l in f:
                    l = map(int, l.rstrip().split(",")[:2])
                    g.add_edge(int(l[0]), int(l[1]))

                db_net = load_data("data/db/%s/net" % token)

                r = db_net
                r['net'] = {'g': g, 'name': net_name}
                db_net = r
                db_net.close()

                conf = {'nodes': {}, 'edges': {}, 'model': {}, 'status': {}}

                # Read Configuration
                if os.path.exists("%s/nodes.csv" % base_path):
                    conf['nodes']['profile'] = {}
                    conf['nodes']['threshold'] = {}
                    f = open("%s/nodes.csv" % base_path)
                    for l in f:
                        l = l.rstrip().split(",")
                        conf['nodes']['threshold'][int(l[0])] = float(l[1])
                        conf['nodes']['profile'][int(l[0])] = float(l[2])

                if os.path.exists("%s/nodes_initial_status.csv" % base_path):
                    conf['status'] = {'Infected': [], 'Blocked': []}
                    f = open("%s/nodes_initial_status.csv" % base_path)
                    for l in f:
                        l = l.rstrip().split(",")
                        node = int(l[0])
                        nstatus = int(l[1])
                        if nstatus == 1:
                            conf['status']['Infected'].append(node)

                        if nstatus == -1:
                            conf['status']['Blocked'].append(node)

                if os.path.exists("%s/edges.csv" % base_path):
                    f = open("%s/edges.csv" % base_path)
                    for l in f:
                        l = l.rstrip().split(",")
                        conf['edges'].append({'source': int(l[0]), 'target': int(l[1]), 'weight': float(l[2])})

                if len(conf) > 0:
                    db_conf = load_data("data/db/%s/configuration" % token)
                    db_conf['configuration'] = conf
                    db_conf.close()

                return {'Message': 'Exploratory configuration loaded'}, success

            except:
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


api.add_resource(Configure, '/api/Configure')
api.add_resource(Graph, '/api/GetGraph')
api.add_resource(Generators, '/api/Generators')
api.add_resource(Networks, '/api/Networks')
api.add_resource(ERGraph, '/api/Generators/ERGraph')
api.add_resource(PlantedPartition, '/api/Generators/PlantedPartition')
api.add_resource(BarabasiAlbertGraph, '/api/Generators/BarabasiAlbertGraph')
api.add_resource(ClusteredBarabasiAlbertGraph, '/api/Generators/ClusteredBarabasiAlbertGraph')
api.add_resource(WattsStrogatzGraph, '/api/Generators/WattsStrogatzGraph')
api.add_resource(CompleteGraph, '/api/Generators/CompleteGraph')
api.add_resource(IndependentCascades, '/api/IndependentCascades')
api.add_resource(Models, '/api/Models')
api.add_resource(Threshold, '/api/Threshold')
api.add_resource(KerteszThreshold, '/api/KerteszThreshold')
api.add_resource(SIR, '/api/SIR')
api.add_resource(SI, '/api/SI')
api.add_resource(SIS, '/api/SIS')
api.add_resource(SEIS, '/api/SEIS')
api.add_resource(SEIR, '/api/SEIR')
api.add_resource(Profile, '/api/Profile')
api.add_resource(ProfileThreshold, '/api/ProfileThreshold')
api.add_resource(CognitiveOpinionDynamic, '/api/CognitiveOpinionDynamic')
api.add_resource(Voter, '/api/Voter')
api.add_resource(QVoter, '/api/QVoter')
api.add_resource(MaJorityRule, '/api/MajorityRule')
api.add_resource(Sznajd, '/api/Sznajd')
api.add_resource(Experiment, '/api/Experiment')
api.add_resource(ExperimentStatus, '/api/ExperimentStatus')
api.add_resource(Iteration, '/api/Iteration')
api.add_resource(IterationBunch, '/api/IterationBunch')
api.add_resource(Exploratory, '/api/Exploratory')
api.add_resource(UploadNetwork, '/api/UploadNetwork')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

