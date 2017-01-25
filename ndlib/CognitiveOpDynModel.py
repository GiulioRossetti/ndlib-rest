from DiffusionModel import DiffusionModel
import numpy as np

__author__ = "Alina Sirbu"
__email__ = "alina.sirbu@unipi.it"


class CognitiveOpDynModel(DiffusionModel):
    """
    Implements the cognitive model of opinion dynamics by Villone et al.
    Model parameters: 
    (1) self.params['I'], external information value in [0,1]; 
    (2) self.params['T_range_min'], a value in [0,1] representing the minimum of the range of initial values for node parameter T;
    (3) self.params['T_range_max'], a value in [0,1] representing the maximum of the range of initial values for node parameter T. If T_range_min>T_range_max they are swapped;
    (4) self.params['B_range_min'], a value in [0,1] representing the minimum of the range of initial values for node parameter B;
    (5) self.params['B_range_max'], a value in [0,1] representing the maximum of the range of initial values for node parameter B. If B_range_min>B_range_max they are swapped;
    (6) self.params['R_fraction_negative'], a value in [0,1] representing the fraction of individuals having the node parameter R=-1;
    (7) self.params['R_fraction_neutral'], a value in [0,1] representing the fraction of individuals having the node parameter R=0;
    (8) self.params['R_fraction_positive'], a value in [0,1] representing the fraction of individuals having the node parameter R=1. The following relation should hold: R_fraction_negative+R_fraction_neutral+R_fraction_positive=1. To achieve this, the fractions selected will be normalised to sum 1.
    Node states are continuous values in [0,1].
    Additional node parameters encode risk sensitivity R in {0,-1,+1}, tendency to communicate B in [0,1], trust towards institutions T in [0,1].  These are stored in the 'cognitive' node parameter.
    The initial state is generated randomly uniformly from the domain defined by model parameters.
    """

    def set_initial_status(self, configuration=None):
        """
        Override behaviour of methods in class DiffusionModel.
        Overwrites initial status using random real values.
        Generates random node profiles.
        """
        super(CognitiveOpDynModel, self).set_initial_status(configuration)

        # set node status
        for node in self.status:
            self.status[node] = np.random.random_sample()
        self.initial_status = self.status.copy()

        # set new node parameters
        self.params['nodes']['cognitive'] = {}

        # first correct the input model parameters and retreive T_range, B_range and R_distribution
        T_range=(self.params['T_range_min'], self.params['T_range_max'])
        if self.params['T_range_min'] > self.params['T_range_max']:
            T_range = (self.params['T_range_max'], self.params['T_range_min'])

        B_range = (self.params['B_range_min'], self.params['B_range_max'])
        if self.params['B_range_min'] > self.params['B_range_max']:
            B_range = (self.params['B_range_max'], self.params['B_range_min'])
        s = float(self.params['R_fraction_negative'] + self.params['R_fraction_neutral'] +
                  self.params['R_fraction_positive'])
        R_distribution = (self.params['R_fraction_negative']/s, self.params['R_fraction_neutral']/s,
                          self.params['R_fraction_positive']/s)

        # then sample parameters from the ranges and distribution
        for node in self.graph.nodes():
            R_prob = np.random.random_sample()
            if R_prob < R_distribution[0]:
                R = -1
            elif R_prob<(R_distribution[0]+R_distribution[1]):
                R = 0
            else:
                R = 1
            # R, B and T parameters in a tuple
            self.params['nodes']['cognitive'][node] = (R,
                                                       B_range[0]+(B_range[1]-B_range[0])*np.random.random_sample(),
                                                       T_range[0]+(T_range[1]-T_range[0])*np.random.random_sample())

    def clean_initial_status(self, valid_status=None):
        for n, s in self.status.iteritems():
            if s > 1 or s < 0:
                self.status[n] = 0

    def iteration(self):
        """
        One iteration changes the opinion of all agents using the following procedure:
        - first all agents communicate with institutional information I using a deffuant like rule
        - then random pairs of agents are selected to interact  (N pairs)
        - interaction depends on state of agents but also internal cognitive structure
        """

        self.clean_initial_status(None)

        actual_status = {node: nstatus for node, nstatus in self.status.iteritems()}

        if self.actual_iteration == 0:
            self.actual_iteration += 1
            return 0, actual_status

        # first interact with I
        I = self.params['I']
        for node in self.graph.nodes():
            T = self.params['nodes']['cognitive'][node][2]
            R = self.params['nodes']['cognitive'][node][0]
            self.status[node] = self.status[node] + T * (I - self.status[node])
            if R == 1:
                self.status[node] = 0.5 * (1 + self.status[node])
            if R == -1:
                self.status[node] *= 0.5

        # then interact with peers
        for i in range(0, self.graph.number_of_nodes()):
            # select a random node
            n1 = self.graph.nodes()[np.random.randint(0, self.graph.number_of_nodes())]

            # select all of the nodes neighbours (no digraph possible)
            neighbours = self.graph.neighbors(n1)

            # select second node - a random neighbour
            n2 = neighbours[np.random.randint(0, len(neighbours))]

            # update status of n1 and n2
            p1 = pow(self.status[n1], 1.0 / self.params['nodes']['cognitive'][n1][1])
            p2 = pow(self.status[n2], 1.0 / self.params['nodes']['cognitive'][n2][1])

            oldn1 = self.status[n1]
            if np.random.random_sample() < p2:  # if node 2 talks, node 1 gets changed
                T1 = self.params['nodes']['cognitive'][n1][2]
                R1 = self.params['nodes']['cognitive'][n1][0]
                self.status[n1] += (1 - T1) * (self.status[n2] - self.status[n1])
                if R1 == 1:
                    self.status[n1] = 0.5 * (1 + self.status[n1])
                if R1 == -1:
                    self.status[n1] *= 0.5

            if np.random.random_sample() < p1:  # if node 1 talks, node 2 gets changed
                T2 = self.params['nodes']['cognitive'][n2][2]
                R2 = self.params['nodes']['cognitive'][n2][0]
                self.status[n2] += (1 - T2) * (oldn1 - self.status[n2])
                if R2 == 1:
                    self.status[n2] = 0.5 * (1 + self.status[n2])
                if R2 == -1:
                    self.status[n2] *= 0.5

        delta = self.status_delta(actual_status)
        self.status = actual_status
        self.actual_iteration += 1
        return self.actual_iteration - 1, delta
