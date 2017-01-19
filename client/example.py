from NDlibClient import NDlibClient

__author__ = 'rossetti'
__license__ = "GPL"
__email__ = "giulio.rossetti@gmail.com"

e = NDlibClient("http://127.0.0.1:5000")
e.create_experiment()

# e.add_barabasi_albert_graph(4000, 10)
e.add_planted_lpartition_graph(30, 35, 0.7, 0.2)
e.add_kertesz_model(0.1, threshold=0.1, blocked=0.2, adopter_rate=0.1)

# res = e.get_iteration_bunch(10)
# for i in res:
#     print i
#     for k in res[i]:
#        print k

# exit()

for it in xrange(0, 10):
    ex = e.get_iteration()
    for m in ex:
        # print it, m, #sum(ex[m]['status'].values())
        print it, ex[m]['status']

print "reset"
e.reset_experiment()
for it in xrange(0, 10):
    ex = e.get_iteration()
    for m in ex:
        # print it, m, #sum(ex[m]['status'].values())
        print it, ex[m]['status']


#e.load_exploratory("Lastfm_rock")
#e.add_threshold_model(0.01)
#for it in xrange(0, 5):
#    ex = e.get_iteration()
#    for m in ex:
#        print it, m, sum(ex[m]['status'].values())

e.destroy_experiment()
