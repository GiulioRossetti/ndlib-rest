from NDlibClient import NDlibClient
__author__ = 'rossetti'
__license__ = "GPL"
__email__ = "giulio.rossetti@gmail.com"

e = NDlibClient("http://127.0.0.1:5000")


# print "indipendent cascades"
# e.create_experiment()
# x = e.add_erdos_renyi_graph(300, 0.01)
# e.add_independent_cascades(0.1)
# tot = 0
# for it in xrange(0, 10):
#     ex = e.get_iteration()
#     for m in ex:
#         print it, len(ex[m]['status'])
#
# e.destroy_experiment()


# e.create_experiment()
# x = e.add_erdos_renyi_graph(300, 0.01)
# e.add_cognitiveopdyn(0.15, 0, 1, 0, 1, 1/3.0, 1/3.0, 1/3.0)
# tot = 0
# for it in xrange(0, 10):
#     ex = e.get_iteration()
#     for m in ex:
#         print it, len(ex[m]['status'])
#
# e.destroy_experiment()

# rivedere i parametri del modello

#
print "ClusteredBA_bottom"
e.create_experiment()
e.load_exploratory("ClusteredBA_bottom")
e.add_kertesz_model(0.01, threshold=1, blocked=0.1, adopter_rate=0)
tot = 0
for it in xrange(0, 10):
    ex = e.get_iteration()
    for m in ex:
        print ex[m]['status']
        blocked = [v for v, k in ex[m]['status'].iteritems() if k == -1]
        if it == 0:
            print blocked
        else:
            tot += sum(ex[m]['status'].values())
            print tot

e.destroy_experiment()

exit()

# rivedere i parametri del modello
print "ClusteredBA_top"
e.create_experiment()
e.load_exploratory("ClusteredBA_top")
e.add_kertesz_model(0.1, threshold=0.1, blocked=0.1, adopter_rate=0.1)
e.add_threshold_model(0.1, threshold=0.16)
tot = 0
for it in xrange(0, 10):
    ex = e.get_iteration()
    for m in ex:
        blocked = [v for v, k in ex[m]['status'].iteritems() if k == -1]
        if it == 0:
            print m, blocked
        else:
            tot += sum(ex[m]['status'].values())
            print m, tot

e.destroy_experiment()

# OK
print "Core"
e.create_experiment()
e.load_exploratory("ToyCore_Com")
e.add_threshold_model(0.1, threshold=0.16)

tot = 0
for it in xrange(0, 30):
    ex = e.get_iteration()
    for m in ex:
        tot += sum(ex[m]['status'].values())
        print tot

e.destroy_experiment()

# OK
print "Periphery"
e.create_experiment()
e.load_exploratory("ToyPeri_Com")
e.add_threshold_model(0.1, threshold=0.16)
tot = 0
for it in xrange(0, 40):
    ex = e.get_iteration()
    for m in ex:
        tot += sum(ex[m]['status'].values())
        print tot

e.destroy_experiment()
