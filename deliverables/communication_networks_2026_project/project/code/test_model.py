"""Deterministic correctness checks independent of Monte Carlo agreement."""
import unittest
import numpy as np
from model import rate, mm1, fcfs_departures, polling_starts, waiting_area, shortest_path


class ModelTests(unittest.TestCase):
    def test_shannon_units(self):
        self.assertAlmostEqual(rate(1e6,0),1e6)

    def test_lecture_example(self):
        q=mm1(20/60,1/2.5)  # lecture PDF pp.104-106; minutes
        self.assertAlmostEqual(q['Ls'],5)
        self.assertAlmostEqual(q['Ws'],15)
        self.assertAlmostEqual(q['Wq'],12.5)

    def test_stability_guard(self):
        for lam in [-1,50,60]:
            with self.assertRaises(ValueError): mm1(lam,50)

    def test_little_and_time_decomposition(self):
        for lam in [0,5,25,49]:
            q=mm1(lam,50)
            self.assertAlmostEqual(q['Ls'],lam*q['Ws'])
            self.assertAlmostEqual(q['Lq'],lam*q['Wq'])
            self.assertAlmostEqual(q['Ws'],q['Wq']+.02)

    def test_fcfs_hand_calculation(self):
        np.testing.assert_allclose(fcfs_departures([1,1.2,4],[1,2,.5]),[2,4,4.5])

    def test_fcfs_vs_scalar_recursion(self):
        rng=np.random.default_rng(7)
        a=np.cumsum(rng.exponential(.1,3000));s=rng.exponential(.08,len(a))
        expected=[];d=0.
        for ai,si in zip(a,s): d=max(ai,d)+si;expected.append(d)
        np.testing.assert_allclose(fcfs_departures(a,s),expected,atol=1e-10)

    def test_polling_boundary(self):
        np.testing.assert_allclose(polling_starts([0,.1,.2,3.01],1,0),[0,1,2,4])

    def test_polling_vs_scalar(self):
        rng=np.random.default_rng(4);a=np.cumsum(rng.exponential(.2,1000))
        cycle=.15;phase=.03;previous=-1;expected=[]
        for x in a:
            visit=max(int(np.ceil((x-phase)/cycle)),previous+1,0)
            expected.append(phase+visit*cycle);previous=visit
        np.testing.assert_allclose(polling_starts(a,cycle,phase),expected)

    def test_occupancy_area_boundaries(self):
        self.assertAlmostEqual(waiting_area(np.array([0.,2.]),np.array([3.,5.]),1,4),4)

    def test_routing_example(self):
        e=[('A','M',100e6,.001),('A','B',1e9,.0002),('B','M',1e9,.0005)]
        p,d=shortest_path(e,'A','M',1e6)
        self.assertEqual(p,['A','B','M']);self.assertAlmostEqual(d,.0027)


if __name__=='__main__': unittest.main(verbosity=2)
