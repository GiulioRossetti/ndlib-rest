import networkx as nx
import random
import math

__author__ = 'Giulio Rossetti'
__license__ = "GPL"
__email__ = "giulio.rossetti@gmail.com"


def planted_partition_graph(l, k, p_in, p_out, seed=None, directed=False):
    """Return the planted l-partition graph.

    This model partitions a graph with n=l*k vertices in
    l groups with k vertices each. Vertices of the same
    group are linked with a probability p_in, and vertices
    of different groups are linked with probability p_out.

    Parameters
    ----------
    l : int
      Number of groups
    k : int
      Number of vertices in each group
    p_in : float
      probability of connecting vertices within a group
    p_out : float
      probability of connected vertices between groups
    seed : int,optional
      Seed for random number generator(default=None)
    directed : bool,optional (default=False)
      If True return a directed graph

    Returns
    -------
    G : NetworkX Graph or DiGraph
      planted l-partition graph

    Raises
    ------
    NetworkXError:
      If p_in,p_out are not in [0,1] or

    See Also
    --------
    random_partition_model

    References
    ----------
    .. [1] A. Condon, R.M. Karp, Algorithms for graph partitioning
        on the planted partition model,
        Random Struct. Algor. 18 (2001) 116-140.

    .. [2] Santo Fortunato 'Community Detection in Graphs' Physical Reports
       Volume 486, Issue 3-5 p. 75-174. http://arxiv.org/abs/0906.0612
    """
    return random_partition_graph([k]*l, p_in, p_out, seed, directed)


def random_partition_graph(sizes, p_in, p_out, seed=None, directed=False):
    """Return the random partition graph with a partition of sizes.

    A partition graph is a graph of communities with sizes defined by
    s in sizes. Nodes in the same group are connected with probability
    p_in and nodes of different groups are connected with probability
    p_out.

    Paramters
    ---------
    sizes : list of ints
      Sizes of groups
    p_in : float
      probability of edges with in groups
    p_out : float
      probability of edges between groups
    directed : boolean optional, default=False
      Whether to create a directed graph
    seed : int optional, default None
      A seed for the random number generator

    Returns
    -------
    G : NetworkX Graph or DiGraph
      random partition graph of size sum(gs)

    Raises
    ------
    NetworkXError
      If p_in or p_out is not in [0,1]

    Notes
    -----
    This is a generalization of the planted-l-partition described in
    [1]_.  It allows for the creation of groups of any size.

    The partition is store as a graph attribute 'partition'.

    References
    ----------
    .. [1] Santo Fortunato 'Community Detection in Graphs' Physical Reports
       Volume 486, Issue 3-5 p. 75-174. http://arxiv.org/abs/0906.0612
       http://arxiv.org/abs/0906.0612
       """
    # Use geometric method for O(n+m) complexity algorithm
    # partition=nx.community_sets(nx.get_node_attributes(G,'affiliation'))
    if not seed is None:
        random.seed(seed)
    if not 0.0 <= p_in <= 1.0:
        raise nx.NetworkXError("p_in must be in [0,1]")
    if not 0.0 <= p_out <= 1.0:
        raise nx.NetworkXError("p_out must be in [0,1]")

    if directed:
        g = nx.DiGraph()
    else:
        g = nx.Graph()
    n = sum(sizes)
    g.add_nodes_from(range(n))
    # start with len(sizes) groups of gnp random graphs with parameter p_in
    # graphs are unioned together with node labels starting at
    # 0, sizes[0], sizes[0]+sizes[1], ...
    next_group = {}  # maps node key (int) to first node in next group
    start = 0
    group = 0
    for n in sizes:
        edges = ((u+start, v+start)
                 for u, v in
                 nx.fast_gnp_random_graph(n, p_in, directed=directed).edges())
        g.add_edges_from(edges)
        next_group.update(dict.fromkeys(range(start, start+n), start+n))
        group += 1
        start += n

    # handle edge cases
    if p_out == 0:
        return g
    if p_out == 1:
        for n in next_group:
            targets = range(next_group[n], len(g))
            g.add_edges_from(zip([n]*len(targets), targets))
            if directed:
                g.add_edges_from(zip(targets, [n]*len(targets)))
        return g
    # connect each node in group randomly with the nodes not in group
    # use geometric method like fast_gnp_random_graph()
    lp = math.log(1.0 - p_out)
    n = len(g)
    if directed:
        for u in range(n):
            v = 0
            while v < n:
                lr = math.log(1.0 - random.random())
                v += int(lr/lp)
                # skip over nodes in the same group as v, including self loops
                if next_group.get(v, n) == next_group[u]:
                    v = next_group[u]
                if v < n:
                    g.add_edge(u, v)
                    v += 1
    else:
        for u in range(n-1):
            v = next_group[u]  # start with next node not in this group
            while v < n:
                lr = math.log(1.0 - random.random())
                v += int(lr/lp)
                if v < n:
                    g.add_edge(u, v)
                    v += 1
    return g