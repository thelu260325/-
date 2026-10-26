"""Global fractional solvers for the paper's *published* multiuser equations.

This implements Eq. (14) (one Bob, maximum Eve power separately at each tap)
and Eq. (15) (maximum Bob power separately at each tap, one Eve). The paper's
sum-of-per-tap-maxima is NOT generally the same as selecting one physical Bob
or one non-colluding Eve for an entire transmission. This implementation keeps
that distinction explicit; it does not silently replace the published model.

For a ratio lambda, Dinkelbach's auxiliary problem separates over taps. For a
fixed candidate Bob b and all Eves e_j, maximize q=6(bw)^2-lambda*pi*e*max_j(e_jw)^2.
Zero is feasible and an overall sign change makes bw nonnegative. The SOCP

    maximize t
    ||[t, sqrt(lambda*pi*e) z]||_2 <= sqrt(6) b w
    z >= +e_j w, z >= -e_j w, ||w||_p <= 1, t,z >= 0

has t^2 = max q. All tap/candidate cones are independent, so maximizing their
sum of t also maximizes each separately. For several Bobs, solve one cone per
candidate Bob and tap, then choose the largest q at each tap. Dinkelbach thus
solves these published equations globally, to the numerical cone solver's
accuracy. This statement concerns the mathematical channel-gain model only,
not physical adequacy, calibrated optical channels or exact published curves.

Requires NumPy, CVXPY and Clarabel. No random initialisation or hidden data.
"""
from __future__ import annotations
from functools import lru_cache
import math
import numpy as np
import cvxpy as cp

PIE = math.pi * math.e


def _p_value(p):
    if p in (1, 1.0, "1"):
        return 1
    if p in (2, 2.0, "2"):
        return 2
    if p in (np.inf, float("inf"), "inf", "infty", "infinity"):
        return np.inf
    raise ValueError("p must be 1, 2 or inf")


def _inputs(HB, HE):
    B, E = np.asarray(HB, dtype=float), np.asarray(HE, dtype=float)
    if B.ndim == 2:
        B = B[None, ...]
    if E.ndim == 2:
        E = E[None, ...]
    if B.ndim != 3 or E.ndim != 3 or B.shape[1:] != E.shape[1:]:
        raise ValueError("HB and HE must have compatible (K,S,NF) shapes")
    if min(B.shape) < 1 or min(E.shape) < 1:
        raise ValueError("Empty channel arrays are not supported")
    if B.shape[0] > 1 and E.shape[0] > 1:
        raise ValueError("Eq14/15 implementation supports multiple Bobs OR multiple Eves")
    if not np.all(np.isfinite(B)) or not np.all(np.isfinite(E)):
        raise ValueError("Channel arrays must be finite")
    return B, E


def evaluate_multiuser(HB, HE, W, snr_db=20):
    """Evaluate the paper's sum-of-per-tap-maxima metric, without reoptimising."""
    B, E = _inputs(HB, HE)
    W = np.asarray(W, dtype=float)
    if W.shape != (B.shape[2], B.shape[1]):
        raise ValueError("W must have shape (NF,S)")
    bp = np.square(np.einsum("ksn,ns->ks", B, W)).max(axis=0)
    ep = np.square(np.einsum("ksn,ns->ks", E, W)).max(axis=0)
    c = 3 * PIE * 10.0 ** (-float(snr_db) / 10)
    numerator = 6 * float(bp.sum()) + c
    denominator = PIE * float(ep.sum()) + c
    ratio = numerator / denominator
    return {
        "numerator": numerator,
        "denominator": denominator,
        "ratio": ratio,
        "rate": max(0.0, 0.5 * math.log2(ratio)),
        "bob_power": float(bp.sum()),
        "eve_power": float(ep.sum()),
    }


@lru_cache(maxsize=32)
def _graph(kb, ke, S, N, p):
    C = kb * S
    W = cp.Variable((N, C))
    t = cp.Variable(C, nonneg=True)
    z = cp.Variable(C, nonneg=True)
    b = cp.Parameter((N, C))
    es = [cp.Parameter((N, C)) for _ in range(ke)]
    gamma = cp.Parameter(nonneg=True)
    constraints = [
        cp.norm(cp.vstack([t, gamma * z]), p=2, axis=0)
        <= math.sqrt(6) * cp.sum(cp.multiply(b, W), axis=0),
        cp.norm(W, p=p, axis=0) <= 1,
    ]
    for ej in es:
        ew = cp.sum(cp.multiply(ej, W), axis=0)
        constraints.extend([z >= ew, z >= -ew])
    problem = cp.Problem(cp.Maximize(cp.sum(t)), constraints)
    return problem, W, b, es, gamma


def solve_multiuser(HB, HE, snr_db=20, p="inf", tol=1e-6, max_iter=40):
    """Solve Eq14/15; returns W (NF,S), rate, ratio, status and diagnostics.

    HB/HE: (KB,S,NF)/(KE,S,NF), or (S,NF) for a single receiver.
    At most one of KB and KE may exceed 1. Channels should be consistently
    scaled, including the interpretation of the alpha/sigma SNR argument.
    The original constraints are separate ||w_s||_p <= 1 at every tap.
    """
    B, E = _inputs(HB, HE)
    p = _p_value(p)
    kb, S, N = B.shape
    ke = E.shape[0]
    if tol <= 0 or max_iter < 1:
        raise ValueError("tol and max_iter must be positive")
    problem, variable, bpar, epars, gammapar = _graph(kb, ke, S, N, p)
    # Bob-major column order, with all S taps for every candidate.
    bc = B.reshape(kb * S, N).T
    ec = [np.tile(E[j], (kb, 1)).T for j in range(ke)]
    scale = np.maximum(np.linalg.norm(bc, axis=0),
                       np.max(np.stack([np.linalg.norm(x, axis=0) for x in ec]), axis=0))
    scale = np.where(scale > 1e-15, scale, 1.0)
    bpar.value = bc / scale
    for par, actual in zip(epars, ec):
        par.value = actual / scale

    lam = 1.0
    result = None
    statuses = []
    converged = False
    residual = math.inf
    chosen = np.zeros(S, dtype=int)
    for iteration in range(1, max_iter + 1):
        gammapar.value = math.sqrt(lam * PIE)
        problem.solve(solver="CLARABEL", warm_start=True, verbose=False,
                      tol_gap_abs=1e-9, tol_gap_rel=1e-9, tol_feas=1e-9,
                      max_iter=250)
        statuses.append(problem.status)
        if variable.value is None or problem.status not in (cp.OPTIMAL, cp.OPTIMAL_INACCURATE):
            raise RuntimeError(f"Multiuser SOCP failed: {problem.status}")
        wc = np.asarray(variable.value).copy()
        # Remove tiny norm violations before evaluating a feasible lower bound.
        norms = np.linalg.norm(wc, ord=p, axis=0)
        wc /= np.maximum(norms, 1.0)
        bvalue = np.sum(bc * wc, axis=0)
        evalue = np.max(np.abs(np.stack([np.sum(ej * wc, axis=0) for ej in ec])), axis=0)
        q = (6 * bvalue ** 2 - lam * PIE * evalue ** 2).reshape(kb, S)
        chosen = q.argmax(axis=0)
        columns = chosen * S + np.arange(S)
        W = wc[:, columns].copy()
        qbest = q[chosen, np.arange(S)]
        W[:, qbest < 0] = 0.0
        result = evaluate_multiuser(B, E, W, snr_db)
        residual = result["numerator"] - lam * result["denominator"]
        new_lam = result["ratio"]
        if abs(residual) <= tol * max(1.0, result["numerator"], result["denominator"]):
            converged = True
            lam = new_lam
            break
        # A significant drop contradicts an accurate Dinkelbach step.
        if new_lam < lam - 1e-6 * max(1.0, lam):
            raise RuntimeError("Numerically non-monotone Dinkelbach step")
        lam = new_lam
    assert result is not None
    result.update({
        "W": W,
        "iterations": iteration,
        "residual": float(residual),
        "fractional_residual": float(residual),
        "norm_violation": max(0.0, float(np.max(np.linalg.norm(W, ord=p, axis=0))) - 1),
        "status": ("global_model_to_solver_tolerance" if converged and all(s == cp.OPTIMAL for s in statuses)
                   else "converged_inaccurate_cone" if converged else "iteration_limit"),
        "cone_statuses": statuses,
        "selected_bob_per_tap": chosen,
        "metric": "published_sum_of_per_tap_maxima",
    })
    return result


def self_test():
    """Nontrivial regression checks, independently of channel geometry."""
    rng = np.random.default_rng(20261026)
    # Analytical scalar counterexample: best is W=(1,0), not both active.
    B = np.array([[[3.0], [1.0]]])
    E = np.array([[[0.1], [0.7]]])
    ans = solve_multiuser(B, E, snr_db=0, p=2)
    expected = evaluate_multiuser(B, E, np.array([[1.0, 0.0]]), 0)["rate"]
    assert abs(ans["rate"] - expected) < 2e-6, (ans["rate"], expected)
    checks = 1
    B = rng.uniform(0.02, 1.0, (4, 3, 3))
    E = rng.uniform(0.02, 1.0, (4, 3, 3))
    # Nested physical receiver sets -> monotonicity of the *published* metric.
    rb = [solve_multiuser(B[:k], E[:1], 20, 2)["rate"] for k in range(1, 5)]
    re = [solve_multiuser(B[:1], E[:k], 20, 2)["rate"] for k in range(1, 5)]
    assert np.min(np.diff(rb)) >= -2e-5, rb
    assert np.max(np.diff(re)) <= 2e-5, re
    checks += 2
    # Same numerical radius has nested feasible norm balls.
    norm_rates = [solve_multiuser(B[:1], E[:2], 20, p)["rate"] for p in [1, 2, np.inf]]
    assert np.min(np.diff(norm_rates)) >= -2e-5, norm_rates
    checks += 1
    zero = solve_multiuser(np.zeros((1, 2, 2)), np.zeros((1, 2, 2)), 20, 2)
    assert zero["rate"] == 0 and zero["norm_violation"] == 0
    checks += 1
    return {"checks": checks, "scalar_expected_rate": expected,
            "bob_monotonic_rates": rb, "eve_monotonic_rates": re,
            "norm_rates_1_2_inf": norm_rates}


if __name__ == "__main__":
    import json
    print(json.dumps(self_test(), indent=2))
