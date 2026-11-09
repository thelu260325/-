"""Transparent queueing and polling models; time in seconds, size in bits.

No 5G protocol stack or AI classifier is simulated. The radio rate is an
ideal Shannon bound. See the report for assumptions and model boundaries.
"""
from __future__ import annotations
import heapq
import numpy as np


def rate(bandwidth_hz: float, snr_db: float) -> float:
    if bandwidth_hz <= 0:
        raise ValueError("Bandwidth must be positive")
    return bandwidth_hz * np.log2(1.0 + 10.0 ** (snr_db / 10.0))


def mm1(arrival_rate: float, service_rate: float) -> dict:
    if not 0 <= arrival_rate < service_rate:
        raise ValueError("Steady state requires 0 <= lambda < mu")
    rho = arrival_rate / service_rate
    return {"rho": rho, "Ls": rho / (1-rho), "Lq": rho*rho/(1-rho),
            "Ws": 1/(service_rate-arrival_rate),
            "Wq": arrival_rate/(service_rate*(service_rate-arrival_rate)),
            "P0": 1-rho}


def fcfs_departures(arrivals, services):
    """Exact Lindley recursion in O(n), from an initially empty FCFS queue.

    D_i=sum_{j<=i} S_j + max_{k<=i}(A_k-sum_{j<k} S_j).
    The caller must pass sorted arrivals and nonnegative service times.
    """
    a, s = np.asarray(arrivals), np.asarray(services)
    if len(a) != len(s) or np.any(np.diff(a) < 0) or np.any(s < 0):
        raise ValueError("Invalid FCFS inputs")
    if not len(a):
        return np.array([], dtype=float)
    cumulative = np.cumsum(s)
    before = cumulative-s
    return cumulative + np.maximum.accumulate(a-before)


def polling_starts(arrivals, cycle_s, phase_s):
    """One image admitted per reserved visit; unused visits remain idle.

    Visit k is at phase + k*cycle. Images arriving after that instant wait
    for a later visit. Distinct arrivals never share one visit.
    """
    a = np.asarray(arrivals)
    if cycle_s <= 0 or np.any(np.diff(a) < 0):
        raise ValueError("Invalid polling inputs")
    if not len(a):
        return np.array([], dtype=float)
    first = np.maximum(0, np.ceil((a-phase_s)/cycle_s)).astype(np.int64)
    index = np.arange(len(a), dtype=np.int64)
    visits = index + np.maximum.accumulate(first-index)
    return phase_s + visits*cycle_s


def waiting_area(arrivals, departures, t0, t1):
    """Integral of system occupancy over [t0,t1], including boundary jobs."""
    overlap = np.maximum(0., np.minimum(departures,t1)-np.maximum(arrivals,t0))
    return float(overlap.sum())


def shortest_path(edges, source, destination, size_bits):
    """Directed Dijkstra with nonnegative, fixed store-and-forward weights."""
    graph = {}
    for u,v,capacity,prop in edges:
        graph.setdefault(u,[]).append((v,size_bits/capacity+prop))
    heap=[(0.,source,[source])]
    done=set()
    while heap:
        cost,u,path=heapq.heappop(heap)
        if u in done:
            continue
        if u == destination:
            return path,cost
        done.add(u)
        for v,w in graph.get(u,[]):
            heapq.heappush(heap,(cost+w,v,path+[v]))
    raise ValueError("Destination unreachable")
