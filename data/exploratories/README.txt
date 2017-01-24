An exploratory is identified by a folder having name:
    network_exploratory (i.e. Lastfm_rock)

The folder should contain up to three files:

- nodes.csv
  having format:
    id_node,threshold,profile
  Where threshold and profile are ranging in [0,1]. If only one is defined the default value - to be specified for each entry - is 0.

- edges.csv
  having format:
    id_node_from,id_node_to,weight
  Where weight ranges in [0,1]. Default value 1.

- nodes_initial_status.csv
  having format:
    id_node,initial_status
  Where initial_status is a value in [-1, 0, 1, 2] depending by the statuses allowed by the desired model.