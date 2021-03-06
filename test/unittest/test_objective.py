# -*- coding: utf-8 -*-
"""
Tests of the objective module
"""

# needed for python 3 compatibility
from __future__ import division
from abc import ABCMeta  # Metaclass for abstract base classes

# Sometimes it is convenient to run it outside of the unit-testing framework
# in which case the unittesting module is not imported
if __name__ == '__main__':

    class unittest(object):

        class TestCase(object):

            def __init__(self):
                self.setUp()

            def assertEqual(self, first, second):
                print 'are{} equal'.format(' not' if first != second else '')

else:
    try:
        import unittest2 as unittest
    except ImportError:
        import unittest  # @UnusedImport
import os.path
import numpy
import shutil
import quantities as pq
import neo
from nineline.cells.neuron import NineCellMetaClass, simulation_controller
from neurotune import Parameter, Tuner
from neurotune.objective.phase_plane import (PhasePlaneHistObjective,
                                             PhasePlanePointwiseObjective)
from neurotune.objective.spike import (SpikeFrequencyObjective,
                                       SpikeTimesObjective)
from neurotune.algorithm.grid import GridAlgorithm
from neurotune.simulation.nineline import NineLineSimulation
from neurotune.analysis import AnalysedSignal, Analysis
try:
    from matplotlib import pyplot as plt
except:
    plt = None

time_start = 250 * pq.ms
time_stop = 2000 * pq.ms

data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                        '..', 'data', 'objective'))
nineml_file = os.path.join(data_dir, 'Golgi_Solinas08.9ml')

parameter = Parameter('soma.KA.gbar', 'nS', 0.001, 0.015, False)
parameter_range = numpy.linspace(parameter.lbound, parameter.ubound, 15)
simulation = NineLineSimulation(nineml_file)
# Create a dummy tuner to generate the simulation 'setups'
tuner = Tuner([parameter],
              SpikeFrequencyObjective(1, time_start=time_start,
                                            time_stop=time_stop),
              GridAlgorithm(num_steps=[10]),
              simulation)

cache_dir = os.path.join(data_dir, 'cached')
reference_path = os.path.join(cache_dir, 'reference.neo.pkl')
try:
    reference_block = neo.PickleIO(reference_path).read()[0]
    recordings = []
    for p in parameter_range:
        recording = neo.PickleIO(os.path.join(cache_dir,
                                       '{}.neo.pkl'.format(p))).read()[0]
        recordings.append(recording)
except:
    try:
        shutil.rmtree(cache_dir)
    except:
        pass
    print ("Generating test recordings, this may take some time (but will be "
           "cached for future reference)...")
    os.makedirs(cache_dir)
    cell = NineCellMetaClass(nineml_file)()
    cell.record('v')
    print "Simulating reference trace"
    simulation_controller.run(simulation_time=time_stop, timestep=0.025)
    reference_block = cell.get_recording('v', in_block=True)
    neo.PickleIO(reference_path).write(reference_block)
    recordings = []
    for p in parameter_range:
        print "Simulating candidate parameter {}".format(p)
        recording = simulation.run_all([p])
        neo.PickleIO(os.path.join(cache_dir,
                                '{}.neo.pkl'.format(p))).write(recording)
        recordings.append(recording)
    print "Finished regenerating test recordings"

reference = AnalysedSignal(reference_block.segments[0].analogsignals[0]).\
                                                   slice(time_start, time_stop)
analyses = [Analysis(r, simulation.setups) for r in recordings]
analyses_dict = dict([(str(r.annotations['candidate'][0]),
                       Analysis(r, simulation.setups))
                      for r in recordings])


class TestObjective(object):

    # Declare this class abstract to avoid accidental construction
    __metaclass__ = ABCMeta

    def plot(self):
        if not plt:
            raise Exception("Matplotlib not imported properly")
        plt.plot(parameter_range,
                 [self.objective.fitness(a) for a in analyses])
        plt.xlabel('soma.KA.gbar')
        plt.ylabel('fitness')
        plt.title(self.__class__.__name__)
        plt.show()

    def test_fitness(self):
        fitnesses = [self.objective.fitness(a) for a in analyses]
        self.assertEqual(fitnesses, self.target_fitnesses)


class TestPhasePlaneHistObjective(TestObjective, unittest.TestCase):

    target_fitnesses = [0.02015844682551193, 0.018123409598981708,
                        0.013962311575888967, 0.0069441036552407784,
                        0.0023839335328775684, 0.0011445239578201732,
                        0.00030602120322790186, 3.0887216189148659e-06,
                        0.006547149370465518, 0.0076745489061881287,
                        0.0099491858088049737, 0.013118872960859328,
                        0.033487424019271739, 0.036565367845945843,
                        0.039124238259558256]

    def setUp(self):
        self.objective = PhasePlaneHistObjective(reference,
                                                 time_start=time_start,
                                                 time_stop=time_stop)


class TestPhasePlanePointwiseObjective(TestObjective, unittest.TestCase):

    target_fitnesses = [791688.05737917486, 417417.7464231535,
                        193261.77390985735, 74410.720655699188,
                        22002.548124354013, 3708.9743763776464,
                        181.9806266596876, 1.6331237044696623e-33,
                        178.61862070496014, 3635.6582762656681,
                        20987.897851732858, 71968.838988315663,
                        187877.22081095798, 403248.13347720244,
                        761436.21907631645]

    def setUp(self):
        self.objective = PhasePlanePointwiseObjective(reference,
                                                      (20, -20), 100,
                                                      time_start=time_start,
                                                      time_stop=time_stop)


class TestSpikeFrequencyObjective(TestObjective, unittest.TestCase):

    target_fitnesses = [0.3265306122448987, 0.3265306122448987,
                        0.3265306122448987, 0.0, 0.0, 0.0, 0.0, 0.0,
                        0.32653061224489766, 0.32653061224489766,
                        0.32653061224489766, 0.32653061224489766,
                        1.3061224489795906, 1.3061224489795906,
                        1.3061224489795906]

    def setUp(self):
        self.objective = SpikeFrequencyObjective(reference.spike_frequency(),
                                                 time_start=time_start,
                                                 time_stop=time_stop)


class TestSpikeTimesObjective(TestObjective, unittest.TestCase):

    target_fitnesses = [48861.63264168518, 42461.31814161993,
                        45899.285983621434, 71791.87749344285,
                        72317.99719666546, 43638.346161592424,
                        11543.74327161325, 2.6999188118427894e-20,
                        24167.5639638691, 51168.20605556744, 68990.99639960933,
                        54978.101362379784, 60117.67140614826,
                        55935.42039310986, 58535.24894951394]

    def setUp(self):
        self.objective = SpikeTimesObjective(reference.spike_times(),
                                             time_start=time_start,
                                             time_stop=time_stop)

if __name__ == '__main__':

#     import cPickle as pkl
#
#     test = TestPhasePlanePointwiseObjective()
#     ka_tests = ['0.00437931034483', '0.00486206896552', '0.00534482758621']
#     sk2_tests = ['0.0447916666667', '0.0458333333333', '0.0489583333333']
#
    parameters = [Parameter('soma.KA.gbar', 'nS', 0.001, 0.015, False),
                   Parameter('soma.SK2.gbar', 'nS', 0.001, 0.015, False)]
#     simulation = NineLineSimulation(nineml_file)
#     # Create a dummy tuner to generate the simulation 'setups'
#     tuner = Tuner(parameters,
#                   SpikeFrequencyObjective(1, time_start=time_start,
#                                                 time_stop=time_stop),
#                   GridAlgorithm(num_steps=[10, 10]),
#                   simulation)
#
#     for ka_test in ka_tests:
#         for sk2_test in sk2_tests:
#             with open('/home/tclose/Data/NeuroTune/'
#                       'evaluate_grid.2014-05-27-Tuesday_12-45-29.1'
#                       '/recordings/recordingssoma.'
#                       'KA.gbar={},soma.SK2.gbar={}.neo.pkl'
#                       .format(ka_test, sk2_test)) as f:
#                 data = pkl.load(f)
#             sig = data.segments[0].analogsignals[0]
# #             plt.plot(sig.times, sig)
# #             plt.show()
#             analysis = Analysis(data, simulation.setups)
#             fitness = test.objective.fitness(analysis)
#             print "ka {}, sk2 {}: {}".format(ka_test, sk2_test, fitness)

    from neurotune.objective.multi import MultiObjective
    # Generate the reference trace from the original class
#     cell = NineCellMetaClass(nineml_file)()
#     cell.record('v')
#     simulation_controller.run(simulation_time=2000 * pq.ms,
#                               timestep=0.025)
#     reference = AnalysedSignal(cell.get_recording('v'))
#     sliced_reference = reference.slice(500 * pq.ms, 2000 * pq.ms)

    # Instantiate the multi-objective objective from 3 phase-plane objectives
    objective = MultiObjective(PhasePlaneHistObjective(reference),
                               PhasePlanePointwiseObjective(reference,
                                                            (20, -20), 100),
                               SpikeFrequencyObjective(reference.\
                                                       spike_frequency()),
                               SpikeTimesObjective(reference.spikes()))
    simulation = NineLineSimulation(nineml_file)
    # Instantiate the tuner
    tuner = Tuner(parameters,
                  objective,
                  GridAlgorithm([10, 10]),
                  simulation)

    analysis = Analysis(simulation.run_all([0.00196552, 0.05024138]),
                        simulation.setups)
    objective.fitness(analysis)

#     for TestClass in [TestPhasePlaneHistObjective,
#                       TestPhasePlanePointwiseObjective,
#                       TestSpikeFrequencyObjective,
#                       TestSpikeTimesObjective]:
#         test = TestClass()
#         print TestClass.__name__ + ': ' + repr([test.objective.fitness(a)
#                                                 for a in analyses])
#         test.plot()
