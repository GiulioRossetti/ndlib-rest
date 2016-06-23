from NDlibClient import NDlibClient

__author__ = 'rossetti'
__license__ = "GPL"
__email__ = "giulio.rossetti@gmail.com"

e = NDlibClient("http://kddsna.isti.cnr.it:5000")
e.create_experiment()

#e.add_barabasi_albert_graph(4000, 10)
#e.add_threshold_model(0.01)
#for it in xrange(0, 20):
#    ex = e.get_iteration()
#    for m in ex:
#        print it, m, sum(ex[m]['status'].values())

e.load_exploratory("Lastfm_rock")
e.add_threshold_model(0.01)
for it in xrange(0, 5):
    ex = e.get_iteration()
    for m in ex:
        print it, m, sum(ex[m]['status'].values())

e.destroy_experiment()
