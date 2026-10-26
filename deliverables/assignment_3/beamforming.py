"""Globally solved beamforming models for Wang et al. (2024), Eq. (10)/(16).

Arrays HB and HE have shape (S, NF); W has shape (NF, S). The caller
must use a SINGLE common channel/noise normalization. snr_db means
20*log10(alpha/sigma), so c = 3*pi*e*10**(-snr_db/10).

The optimized ratio is (6 sum_s B_s^2+c)/(pi*e sum_s E_s^2+c).
For spherical, independently selectable tap uncertainty, B_s is
max(|HB_s w_s|-eps_b[s]*||w_s||_2, 0) and E_s is
|HE_s w_s|+eps_e[s]*||w_s||_2. These extrema are exact for Eq. (17),
not a stochastic approximation and not a physical position-error model.

Method: Dinkelbach's scalar fractional iteration. Each parameterized
subproblem separates into S independent maximizations of B_s^2-lambda E_s^2
(with sqrt(6) and sqrt(pi*e) included). Perfect-CSI subproblems are solved
analytically: a largest eigenvector for p=2, and all vertex-pair segments
of the p=1/infinity ball for polyhedral constraints. The latter is exact:
the feasible image (HB_s w, HE_s w) is a 2-D polygon, whose indefinite
quadratic maximum is on an edge, and all polygon edges are included.

Robust subproblems are GLOBAL convex SOCPs after fixing the harmless
sign HB_s w>=0. Introduce t,z>=0 and enforce
    ||[t,sqrt(lambda)*z]||_2 + eps_b*||w||_2 <= HB_s w,
    z >= |HE_s w| + eps_e*||w||_2,  ||w||_p <= 1.
Maximizing t maximizes the nonnegative quadratic difference t^2; w=0
ensures a nonnegative optimum. Independent tap cones are batched in one
problem and maximizing sum(t_s) maximizes each t_s simultaneously.
All global-optimum statements are to floating-point/conic-solver tolerance;
status/residuals must be retained. This is an alternative exact method for
the paper's model, NOT a claim to reproduce its printed Algorithm 1.

No CVXPY dependency is needed for perfect CSI or zero forcing. For robust
CSI use the environment's CVXPY+Clarabel. Run ``python beamforming.py``
for numerical self-tests. No channel generation or plotting lives here.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import product
import numpy as np
from scipy.optimize import linprog

PI_E = float(np.pi * np.e)


def _validate(HB, HE):
    hb = np.asarray(HB, dtype=float)
    he = np.asarray(HE, dtype=float)
    if hb.ndim == 1:
        hb = hb[None, :]
    if he.ndim == 1:
        he = he[None, :]
    if hb.ndim != 2 or he.shape != hb.shape or min(hb.shape) < 1:
        raise ValueError('HB and HE must share nonempty shape (S,NF).')
    if not np.isfinite(hb).all() or not np.isfinite(he).all():
        raise ValueError('Channels must be finite.')
    return hb, he


def _p_value(p):
    if isinstance(p, str) and p.lower() in ('inf', 'infinity', 'infty'):
        return np.inf
    if p in (1, 2, np.inf):
        return p
    raise ValueError('p must be 1, 2, or numpy.inf.')


def _radii(value, S):
    x = np.broadcast_to(np.asarray(value, dtype=float), (S,)).copy()
    if np.any(x < 0) or not np.isfinite(x).all():
        raise ValueError('Uncertainty radii must be finite and nonnegative.')
    return x


def _noise(snr_db):
    c = float(3 * PI_E * 10.0 ** (-float(snr_db) / 10.0))
    if not np.isfinite(c) or c <= 0:
        raise ValueError('snr_db must yield finite, positive noise.')
    return c


def _norms(W, p):
    return np.linalg.norm(W, ord=p, axis=0)


def _project_radial(W, p):
    return W / np.maximum(1.0, _norms(W, p))[None, :]


def effective_gains(HB, HE, W, eps_b=0.0, eps_e=0.0):
    """Return exact per-tap worst-case signal amplitudes (B,E)."""
    hb, he = _validate(HB, HE)
    w = np.asarray(W, dtype=float)
    if w.shape != (hb.shape[1], hb.shape[0]) or not np.isfinite(w).all():
        raise ValueError('W must be finite with shape (NF,S).')
    eb, ee = _radii(eps_b, len(hb)), _radii(eps_e, len(hb))
    n2 = _norms(w, 2)
    b = np.maximum(np.abs(np.sum(hb.T * w, axis=0)) - eb * n2, 0.0)
    e = np.abs(np.sum(he.T * w, axis=0)) + ee * n2
    return b, e


def evaluate_metrics(HB, HE, W, snr_db, eps_b=0.0, eps_e=0.0):
    """Rate in bits/s/Hz plus the exact objective numerator/denominator."""
    b, e = effective_gains(HB, HE, W, eps_b, eps_e)
    c = _noise(snr_db)
    numerator = float(6.0 * np.dot(b, b) + c)
    denominator = float(PI_E * np.dot(e, e) + c)
    ratio = numerator / denominator
    raw_rate = float(0.5 * np.log2(ratio))
    return dict(rate=max(raw_rate, 0.0), raw_rate=raw_rate, ratio=ratio,
                numerator=numerator, denominator=denominator,
                bob_energy=float(np.dot(b, b)), eve_energy=float(np.dot(e, e)))


def evaluate_rate(HB, HE, W, snr_db, eps_b=0.0, eps_e=0.0):
    """Clipped Eq. (9) secrecy rate, bits/s/Hz."""
    return evaluate_metrics(HB, HE, W, snr_db, eps_b, eps_e)['rate']


@lru_cache(maxsize=20)
def _polytope_vertices(n, p):
    if p == 1:
        V = np.concatenate((np.eye(n), -np.eye(n)), axis=0)
    elif np.isinf(p):
        if n > 10:
            raise ValueError('Exact cube enumeration is limited to NF<=10.')
        V = np.asarray(list(product((-1.0, 1.0), repeat=n)))
    else:
        raise ValueError('Polytope vertices only exist here for p=1 or infinity.')
    ii, jj = np.triu_indices(len(V), 1)
    return V, ii, jj


def _perfect_subproblem(hb, he, lam, p):
    """Exact independent maximizers of 6*(hb.w)^2-lam*pi*e*(he.w)^2."""
    S, n = hb.shape
    W = np.zeros((n, S))
    if p == 2:
        for s in range(S):
            Q = 6.0 * np.outer(hb[s], hb[s]) - lam * PI_E * np.outer(he[s], he[s])
            scale = float(np.max(np.abs(Q)))
            if scale == 0:
                continue
            vals, vecs = np.linalg.eigh(Q / scale)
            if vals[-1] > 0:
                w = vecs[:, -1]
                q = 6 * np.dot(hb[s], w) ** 2 - lam * PI_E * np.dot(he[s], w) ** 2
                if q > 0:
                    W[:, s] = w
        return W
    V, ii, jj = _polytope_vertices(n, p)
    delta = V[jj] - V[ii]
    for s in range(S):
        av = np.sqrt(6.0) * (V @ hb[s])
        bv = np.sqrt(lam * PI_E) * (V @ he[s])
        qv = av * av - bv * bv
        best_i = int(np.argmax(qv))
        best_q = max(0.0, float(qv[best_i]))
        if best_q > 0:
            W[:, s] = V[best_i]
        da, db = av[jj] - av[ii], bv[jj] - bv[ii]
        aa = da * da - db * db
        bb = 2 * (av[ii] * da - bv[ii] * db)
        concave = aa < 0
        tt = np.zeros_like(aa)
        np.divide(-bb, 2 * aa, out=tt, where=concave)
        valid = concave & (tt > 0) & (tt < 1)
        if not np.any(valid):
            continue
        indices = np.flatnonzero(valid)
        t = tt[indices]
        aq = av[ii[indices]] + t * da[indices]
        bq = bv[ii[indices]] + t * db[indices]
        qq = aq * aq - bq * bq
        k = int(np.argmax(qq))
        if qq[k] > best_q:
            j = indices[k]
            W[:, s] = V[ii[j]] + tt[j] * delta[j]
    return W


@lru_cache(maxsize=24)
def _socp_template(n, S, p):
    import cvxpy as cp
    W = cp.Variable((n, S))
    t = cp.Variable(S, nonneg=True)
    z = cp.Variable(S, nonneg=True)
    hb = cp.Parameter((n, S))
    he = cp.Parameter((n, S))
    eb = cp.Parameter(S, nonneg=True)
    ee = cp.Parameter(S, nonneg=True)
    root_lam = cp.Parameter(nonneg=True)
    n2 = cp.norm(W, 2, axis=0)
    bw = cp.sum(cp.multiply(hb, W), axis=0)
    ew = cp.sum(cp.multiply(he, W), axis=0)
    cone = cp.norm(cp.vstack([t, root_lam * z]), 2, axis=0)
    constraints = [cp.norm(W, p, axis=0) <= 1,
                   z >= ew + cp.multiply(ee, n2),
                   z >= -ew + cp.multiply(ee, n2),
                   cone + cp.multiply(eb, n2) <= bw]
    problem = cp.Problem(cp.Maximize(cp.sum(t)), constraints)
    assert problem.is_dcp(dpp=True)
    return problem, W, t, z, hb, he, eb, ee, root_lam, constraints


def _robust_subproblem(hb, he, eb, ee, lam, p):
    """Independent exact conic subproblems, solved in a single batch."""
    n, S = hb.shape[1], hb.shape[0]
    Wout = np.zeros((n, S))
    # Exact existence test for a strictly positive quadratic difference.
    # max_{||u||2<=1} a.u-|b.u| = dist(a,[-b,b]); a secure direction exists
    # iff this distance exceeds sqrt(6)*eps_b+sqrt(lam*pi*e)*eps_e.
    # The existence test is independent of p because every direction can be
    # scaled into every norm ball. Removing zero-optimum cones also avoids
    # conic degeneracy at w=t=z=0.
    a = np.sqrt(6.0) * hb
    b = np.sqrt(lam * PI_E) * he
    b2 = np.sum(b * b, axis=1)
    eta = np.zeros(S)
    np.divide(np.sum(a * b, axis=1), b2, out=eta, where=b2 > 0)
    eta = np.clip(eta, -1.0, 1.0)
    distance = np.linalg.norm(a - eta[:, None] * b, axis=1)
    delta = np.sqrt(6.0) * eb + np.sqrt(lam * PI_E) * ee
    roundoff = 32 * np.finfo(float).eps * np.maximum.reduce([
        np.linalg.norm(a, axis=1), np.linalg.norm(b, axis=1), delta])
    positive_possible = distance > delta + roundoff
    idx = np.flatnonzero(positive_possible)
    if len(idx) == 0:
        return Wout, 'analytic_zero', 0.0
    vals = _socp_template(n, len(idx), p)
    problem, wvar, tvar, zvar, hp, ep, bp, eep, lp, constraints = vals
    # Rescaling each independent cone improves conditioning without changing
    # that cone's argmax. It does NOT rescale the physical channel objective.
    scales = np.maximum.reduce([np.linalg.norm(hb[idx], axis=1),
                                np.linalg.norm(he[idx], axis=1), eb[idx], ee[idx]])
    scales = np.maximum(scales, np.finfo(float).tiny)
    hp.value = (np.sqrt(6.0) * hb[idx] / scales[:, None]).T
    ep.value = (np.sqrt(PI_E) * he[idx] / scales[:, None]).T
    bp.value = np.sqrt(6.0) * eb[idx] / scales
    eep.value = np.sqrt(PI_E) * ee[idx] / scales
    lp.value = np.sqrt(lam)
    try:
        problem.solve(solver='CLARABEL', warm_start=True,
                      tol_gap_abs=1e-9, tol_gap_rel=1e-9, tol_feas=1e-9,
                      max_iter=300)
    except Exception as exc:
        raise RuntimeError('Robust SOCP failed in Clarabel; no local fallback used.') from exc
    if problem.status not in ('optimal', 'optimal_inaccurate') or wvar.value is None:
        raise RuntimeError(f'Robust SOCP status {problem.status}; zero is always feasible.')
    residual = max(float(np.max(c.violation())) for c in constraints)
    w = _project_radial(np.asarray(wvar.value), p)
    bw, ew = effective_gains(hb[idx], he[idx], w, eb[idx], ee[idx])
    q = 6.0 * bw * bw - lam * PI_E * ew * ew
    w[:, q <= 0] = 0.0
    Wout[:, idx] = w
    return Wout, problem.status, residual


def solve_beamforming(HB, HE, snr_db, p=2, eps_b=0.0, eps_e=0.0,
                      tol=1e-8, max_iter=80):
    """Solve the sum-of-squared-tap objective globally to numerical tolerance.

    Returns W, clipped rate, ratio, status, convergence flags, residuals.
    eps_b/eps_e can be scalar or length-S radii, in channel units.
    A nonconverged/inaccurate status must not be described as certified.
    """
    hb, he = _validate(HB, HE)
    p = _p_value(p)
    if tol <= 0 or max_iter < 1:
        raise ValueError('tol must be positive and max_iter at least one.')
    S, n = hb.shape
    eb, ee = _radii(eps_b, S), _radii(eps_e, S)
    robust = bool(np.any(eb) or np.any(ee))
    _noise(snr_db)
    lam = 1.0
    best_W = np.zeros((n, S))
    best = evaluate_metrics(hb, he, best_W, snr_db, eb, ee)
    converged = False
    max_cone_residual = 0.0
    inaccurate = False
    fractional_residual = np.inf
    gap = np.inf
    for iteration in range(1, max_iter + 1):
        if robust:
            W, sub_status, cone_residual = _robust_subproblem(hb, he, eb, ee, lam, p)
            inaccurate |= sub_status == 'optimal_inaccurate'
            max_cone_residual = max(max_cone_residual, cone_residual)
        else:
            W = _perfect_subproblem(hb, he, lam, p)
        W = _project_radial(W, p)
        values = evaluate_metrics(hb, he, W, snr_db, eb, ee)
        new_lam = values['ratio']
        gap = values['numerator'] - lam * values['denominator']
        fractional_residual = abs(new_lam - lam) / max(1.0, abs(new_lam))
        if new_lam >= best['ratio']:
            best_W, best = W.copy(), values
        if fractional_residual <= tol:
            converged = True
            break
        if new_lam < lam:
            # A tiny backwards step can be conic/eigen round-off; retain the
            # best feasible solution but do not hide unresolved convergence.
            if fractional_residual <= 10 * tol:
                converged = True
            break
        lam = new_lam
    norm_residual = max(0.0, float(np.max(_norms(best_W, p) - 1.0)))
    prefix = 'global_dinkelbach_socp' if robust else 'global_dinkelbach_analytic'
    status = prefix if converged else prefix + '_not_converged'
    if inaccurate:
        status += '_inaccurate'
    return dict(W=best_W, **best, status=status, converged=converged,
                iterations=iteration, residual=norm_residual,
                constraint_residual=norm_residual,
                conic_constraint_residual=max_cone_residual,
                dinkelbach_residual=float(fractional_residual),
                dinkelbach_gap=float(gap), p=p, robust=robust)


def zf_beamforming(HB, HE, p=2):
    """Maximize useful amplitude per tap subject to HE_s*w_s=0 and lp<=1."""
    hb, he = _validate(HB, HE)
    p = _p_value(p)
    S, n = hb.shape
    W = np.zeros((n, S))
    for s in range(S):
        if p == 2:
            ee = float(np.dot(he[s], he[s]))
            w = hb[s].copy()
            if ee > 0:
                w -= (np.dot(hb[s], he[s]) / ee) * he[s]
            norm = float(np.linalg.norm(w))
            if norm > 1e-12 * max(float(np.linalg.norm(hb[s])), np.finfo(float).tiny):
                W[:, s] = w / norm
        else:
            hb_scale = float(np.linalg.norm(hb[s]))
            if hb_scale == 0:
                continue
            he_scale = float(np.linalg.norm(he[s]))
            objective_h = hb[s] / hb_scale
            eq = (he[s] / he_scale if he_scale > 0 else he[s])[None, :]
            if p == 1:
                # w is unrestricted, u>=|w|, sum(u)<=1.
                objective = np.r_[-objective_h, np.zeros(n)]
                A = np.r_[np.c_[np.eye(n), -np.eye(n)],
                          np.c_[-np.eye(n), -np.eye(n)],
                          np.r_[np.zeros(n), np.ones(n)][None, :]]
                b = np.r_[np.zeros(2 * n), 1.0]
                result = linprog(objective, A_ub=A, b_ub=b,
                                 A_eq=np.c_[eq, np.zeros((1, n))], b_eq=[0.0],
                                 bounds=[(None, None)] * n + [(0, None)] * n,
                                 method='highs')
            else:
                result = linprog(-objective_h, A_eq=eq, b_eq=[0.0],
                                 bounds=[(-1, 1)] * n, method='highs')
            if not result.success:
                raise RuntimeError(f'ZF LP failed: {result.message}')
            W[:, s] = result.x[:n]
    return _project_radial(W, p)


def solve_zf(HB, HE, snr_db, p=2, eps_b=0.0, eps_e=0.0):
    """Nominal ZF design, optionally evaluated with worst-case uncertainty."""
    hb, he = _validate(HB, HE)
    p = _p_value(p)
    W = zf_beamforming(hb, he, p)
    return dict(W=W, **evaluate_metrics(hb, he, W, snr_db, eps_b, eps_e),
                status='nominal_zf',
                residual=max(0.0, float(np.max(_norms(W, p) - 1.0))),
                nulling_residual=float(np.max(np.abs(np.sum(he.T * W, axis=0)))))


def self_test(include_robust=True):
    """Meaningful model, exact-solution, feasibility and uncertainty checks."""
    rng = np.random.default_rng(20261026)
    report = {}
    hb = rng.uniform(0.1, 1.0, (3, 4))
    he = rng.uniform(0.1, 1.0, (3, 4))
    for p in (1, 2, np.inf):
        out = solve_beamforming(hb, he, 20, p)
        assert out['converged'] and out['constraint_residual'] < 1e-9, out
        zf = solve_zf(hb, he, 20, p)
        assert zf['nulling_residual'] < 1e-8
        assert out['rate'] + 1e-7 >= zf['rate']
        # Exact HE=0 formula: dual norm gives the maximum hb.w.
        dual = np.inf if p == 1 else (1 if np.isinf(p) else 2)
        hnorm = np.linalg.norm(hb, ord=dual, axis=1)
        expected = 0.5 * np.log2(1 + 6 * np.dot(hnorm, hnorm) / _noise(20))
        empty_eve = solve_beamforming(hb, np.zeros_like(he), 20, p)
        assert abs(empty_eve['rate'] - expected) < 1e-8
        identical = solve_beamforming(hb, hb, 20, p)
        assert identical['rate'] < 1e-9
        report[f'perfect_p{p}'] = out['rate']
    assert report['perfect_p1'] <= report['perfect_p2'] + 1e-8
    assert report['perfect_p2'] <= report['perfect_pinf'] + 1e-8
    # Brute-force grid on a 2-D cube verifies the polyhedral quadratic oracle.
    h2, e2 = np.array([[1.1, 0.4]]), np.array([[0.3, 0.8]])
    x = np.linspace(-1, 1, 501)
    xx, yy = np.meshgrid(x, x)
    grid = np.c_[xx.ravel(), yy.ravel()]
    for lam in (1.0, 3.0, 12.0):
        w = _perfect_subproblem(h2, e2, lam, np.inf)[:, 0]
        actual = 6 * (h2[0] @ w) ** 2 - lam * PI_E * (e2[0] @ w) ** 2
        brute = np.max(6 * (grid @ h2[0]) ** 2 - lam * PI_E * (grid @ e2[0]) ** 2)
        assert actual >= brute - 1e-9
        assert actual - brute < 1e-3
    report['polytope_grid_checked'] = True
    if include_robust:
        for p in (1, 2, np.inf):
            exact = solve_beamforming(hb, he, 20, p)
            robust = solve_beamforming(hb, he, 20, p, eps_b=0.02, eps_e=0.04)
            worse = solve_beamforming(hb, he, 20, p, eps_b=0.04, eps_e=0.08)
            assert robust['converged'] and worse['converged'], (robust, worse)
            assert robust['conic_constraint_residual'] < 1e-6
            assert exact['rate'] + 1e-6 >= robust['rate']
            assert robust['rate'] + 1e-6 >= worse['rate']
            assert robust['constraint_residual'] < 1e-9
            # Sample admissible uncertainties: true rates cannot go below the
            # exact independent-sphere worst-case value for a FIXED W.
            for _ in range(50):
                db = rng.normal(size=hb.shape)
                de = rng.normal(size=he.shape)
                db *= (0.02 * rng.random((len(hb), 1)) / np.linalg.norm(db, axis=1)[:, None])
                de *= (0.04 * rng.random((len(he), 1)) / np.linalg.norm(de, axis=1)[:, None])
                sampled = evaluate_rate(hb + db, he + de, robust['W'], 20)
                assert sampled + 1e-8 >= robust['rate']
            report[f'robust_p{p}'] = robust['rate']
        # With no uncertainty, the conic oracle must match the exact oracle.
        wa, ws = _perfect_subproblem(hb, he, 2.5, 2), _robust_subproblem(
            hb, he, np.zeros(len(hb)), np.zeros(len(hb)), 2.5, 2)[0]
        def qs(w):
            b, e = effective_gains(hb, he, w)
            return 6 * b*b - 2.5 * PI_E * e*e
        assert np.max(np.abs(qs(wa)-qs(ws))) < 1e-5
        report['conic_matches_analytic'] = True
    return report


if __name__ == '__main__':
    import json
    print(json.dumps(self_test(), indent=2))
