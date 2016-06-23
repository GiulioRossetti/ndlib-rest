An exploratory is identified by a folder having name:
    network_exploratory (i.e. Lastfm_rock)

The folder should contain two files:

- nodes.csv
  having format:
    id_node,threshold,profile
  Where threshold and profile are ranging in [0,1]. If only one is defined the default value - to be specified for each entry - is 0.

- edges.csv
  having format:
    id_node_from,id_node_to,weight
  Where weight ranges in [0,1]. Default value 1.