"""Deterministic finite-element indoor VLC channel, with explicit assumptions.

This is an independently specified Barry-style model, not an exact reproduction
of Wang et al. (2024): that paper does not give all optical and timing inputs.
See channel_assumptions.md. Channel matrices have shape (symbols, fixtures).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from functools import lru_cache
import json
import math
from typing import Sequence

import numpy as np
from scipy.sparse import csr_matrix

C_LIGHT = 299_792_458.0


@dataclass(frozen=True)
class ChannelConfig:
    """Inputs in SI units; every value absent from the paper is documented."""

    room: tuple[float, float, float] = (10.0, 10.0, 5.0)
    fixture_centres: tuple[tuple[float, float, float], ...] = (
        (-2.5, -2.5, 5.0), (-2.5, 2.5, 5.0),
        (2.5, -2.5, 5.0), (2.5, 2.5, 5.0),
    )
    leds_per_side: int = 5
    led_pitch: float = 0.1
    led_power: float = 2.6
    pd_area: float = 1e-4
    half_power_angle_deg: float = 60.0
    fov_deg: float = 85.0
    refractive_index: float = 1.5
    responsivity: float = 0.53
    wall_reflectivity: float = 0.6
    wall_patch_size: float = 1.0
    time_step: float = 0.5e-9
    symbol_period: float = 10e-9
    max_reflections: int = 4
    seed: int = 20261026

    def __post_init__(self) -> None:
        if len(self.room) != 3 or min(self.room) <= 0:
            raise ValueError('room must contain three positive lengths')
        if not self.fixture_centres:
            raise ValueError('at least one fixture is required')
        if self.leds_per_side < 1 or self.led_pitch < 0 or self.led_power <= 0:
            raise ValueError('invalid LED geometry or power')
        if not 0 < self.half_power_angle_deg < 90:
            raise ValueError('half power angle must lie in (0,90) degrees')
        if not 0 < self.fov_deg <= 90:
            raise ValueError('receiver FoV must lie in (0,90] degrees')
        if self.pd_area <= 0 or self.refractive_index <= 0 or self.responsivity <= 0:
            raise ValueError('positive detector area, refractive index and responsivity required')
        if not 0 <= self.wall_reflectivity < 1:
            raise ValueError('wall reflectivity must lie in [0,1)')
        if min(self.wall_patch_size, self.time_step, self.symbol_period) <= 0:
            raise ValueError('positive spatial and temporal steps required')
        if not 0 <= self.max_reflections <= 6:
            raise ValueError('this implementation supports orders zero through six')

    @property
    def lambertian_order(self) -> float:
        return -math.log(2) / math.log(math.cos(math.radians(self.half_power_angle_deg)))

    @property
    def concentrator_gain(self) -> float:
        return self.refractive_index**2 / math.sin(math.radians(self.fov_deg))**2

    @property
    def fixture_count(self) -> int:
        return len(self.fixture_centres)

    @property
    def leds_per_fixture(self) -> int:
        return self.leds_per_side**2


def _wall_elements(config: ChannelConfig) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Centres, inward unit normals, exact areas of four vertical walls.

    ceil(length/target_width) ensures the final tiling covers each entire wall;
    all tiles on a given wall have equal area and no tile exceeds target width.
    """
    width, length, height = config.room
    centres, normals, areas = [], [], []
    nz = max(1, math.ceil(height / config.wall_patch_size))
    zs = (np.arange(nz) + 0.5) * height / nz
    for normal_axis, extent in ((0, length), (1, width)):
        nh = max(1, math.ceil(extent / config.wall_patch_size))
        hs = -extent / 2 + (np.arange(nh) + 0.5) * extent / nh
        wall_position = (width if normal_axis == 0 else length) / 2
        for side in (-1.0, 1.0):
            for h in hs:
                for z in zs:
                    centre = [0.0, 0.0, z]
                    centre[normal_axis] = side * wall_position
                    centre[1 - normal_axis] = h
                    normal = [0.0, 0.0, 0.0]
                    normal[normal_axis] = -side
                    centres.append(centre)
                    normals.append(normal)
                    areas.append((extent / nh) * (height / nz))
    return np.asarray(centres), np.asarray(normals), np.asarray(areas)


def los_gain(led_position: Sequence[float], receiver_position: Sequence[float],
             config: ChannelConfig = ChannelConfig()) -> float:
    """Single downward LED/upward PD gain, including P, R and concentrator G.

    This implements paper Eq. (1),(2),(5); spectral reflectivity is not needed
    for the direct term. The output is received amperes at unit modulation.
    """
    delta = np.asarray(receiver_position, float) - np.asarray(led_position, float)
    distance = float(np.linalg.norm(delta))
    if distance <= 0:
        return 0.0
    cos_emission = -delta[2] / distance
    cos_incidence = cos_emission
    if cos_emission <= 0 or cos_incidence + 1e-15 < math.cos(math.radians(config.fov_deg)):
        return 0.0
    optical = ((config.lambertian_order + 1) * config.pd_area
               * cos_emission**config.lambertian_order * cos_incidence
               / (2 * math.pi * distance**2))
    return optical * config.led_power * config.responsivity * config.concentrator_gain


class VLCChannel:
    """Precompute wall-emission histories once; reuse them for any floor PD.

    An impulse at a wall element is diffuse reradiated optical power. Each
    propagation carries the physical view factor, the destination reflectivity,
    and a fractional-bin flight delay. The transition is a sum of sparse
    delay-indexed matrices, not a stochastic walk or an order-dependent fit.
    """

    def __init__(self, config: ChannelConfig | None = None) -> None:
        self.config = config or ChannelConfig()
        self.patch_positions, self.patch_normals, self.patch_areas = _wall_elements(self.config)
        c = self.config
        offsets = (np.arange(c.leds_per_side) - (c.leds_per_side - 1) / 2) * c.led_pitch
        self.led_positions = np.asarray([
            [(x + dx, y + dy, z) for dx in offsets for dy in offsets]
            for x, y, z in c.fixture_centres
        ], dtype=float)
        w, length, height = c.room
        if (np.abs(self.led_positions[:, :, 0]) >= w / 2).any() or (
                np.abs(self.led_positions[:, :, 1]) >= length / 2).any():
            raise ValueError('all LED elements must lie strictly within ceiling footprint')
        if not np.allclose(self.led_positions[:, :, 2], height):
            raise ValueError('this model assumes downward fixtures on the ceiling')
        diagonal = math.sqrt(sum(a*a for a in c.room))
        # A path through l walls has l+1 free-space segments; each is <= diagonal.
        self.time_count = math.ceil(((c.max_reflections + 1) * diagonal / C_LIGHT)
                                   / c.time_step) + 2 * (c.max_reflections + 1) + 3
        self.absolute_times = np.arange(self.time_count) * c.time_step
        self.transition_energy_max = 0.0
        self.patch_histories: list[np.ndarray] = []
        if c.max_reflections:
            kernels = self._transition_kernels()
            first = self._source_to_wall()
            self.patch_histories.append(first)
            for _order in range(2, c.max_reflections + 1):
                previous = self.patch_histories[-1]
                current = np.zeros_like(previous)
                for delay, kernel in kernels:
                    if delay >= self.time_count:
                        continue
                    # Shape P x ((T-delay)*F); CSR product skips zero view factors.
                    part = previous[:, :self.time_count-delay, :]
                    propagated = kernel @ part.reshape(len(self.patch_positions), -1)
                    current[:, delay:, :] += propagated.reshape(part.shape)
                self.patch_histories.append(current)
        self._assert_physical_state()

    def _transition_kernels(self) -> list[tuple[int, csr_matrix]]:
        c = self.config
        p = self.patch_positions
        # axis0 = destination, axis1 = source
        delta = p[:, None, :] - p[None, :, :]
        distance = np.linalg.norm(delta, axis=2)
        np.fill_diagonal(distance, np.inf)
        unit = delta / distance[:, :, None]
        cos_out = np.einsum('qpd,pd->qp', unit, self.patch_normals)
        cos_in = -np.einsum('qpd,qd->qp', unit, self.patch_normals)
        transfer = (c.wall_reflectivity * self.patch_areas[:, None]
                    * np.maximum(cos_out, 0) * np.maximum(cos_in, 0)
                    / (math.pi * distance**2))
        self.transition_energy_max = float(np.max(transfer.sum(axis=0), initial=0))
        # Do not normalise a geometric quadrature to force an energy check to pass.
        if self.transition_energy_max > c.wall_reflectivity * 1.02 + 1e-14:
            raise ValueError('wall quadrature overestimates energy; reduce wall_patch_size')
        rows, cols = np.nonzero(transfer > 0)
        delay = distance[rows, cols] / (C_LIGHT * c.time_step)
        lower = np.floor(delay).astype(int)
        fractional = delay - lower
        result = []
        for d in np.unique(np.r_[lower, lower + 1]):
            low = lower == d
            high = lower + 1 == d
            rr = np.r_[rows[low], rows[high]]
            cc = np.r_[cols[low], cols[high]]
            values = np.r_[transfer[rows[low], cols[low]] * (1-fractional[low]),
                           transfer[rows[high], cols[high]] * fractional[high]]
            kernel = csr_matrix((values, (rr, cc)), shape=transfer.shape)
            kernel.eliminate_zeros()
            result.append((int(d), kernel))
        return result

    def _source_to_wall(self) -> np.ndarray:
        c = self.config
        count = len(self.patch_positions)
        result = np.zeros((count, self.time_count, c.fixture_count))
        for fixture in range(c.fixture_count):
            delta = self.patch_positions[:, None, :] - self.led_positions[fixture][None, :, :]
            distance = np.linalg.norm(delta, axis=2)
            unit = delta / distance[:, :, None]
            cos_out = np.maximum(-unit[:, :, 2], 0)
            cos_in = np.maximum(-np.einsum('pid,pd->pi', unit, self.patch_normals), 0)
            weights = ((c.lambertian_order+1) * c.led_power * c.wall_reflectivity
                       * self.patch_areas[:, None] * cos_out**c.lambertian_order
                       * cos_in / (2*math.pi*distance**2))
            delay = distance / (C_LIGHT*c.time_step)
            low = np.floor(delay).astype(int)
            fractional = delay-low
            ids = np.broadcast_to(np.arange(count)[:, None], low.shape)
            np.add.at(result[:, :, fixture], (ids, low), weights*(1-fractional))
            np.add.at(result[:, :, fixture], (ids, low+1), weights*fractional)
        return result

    def _assert_physical_state(self) -> None:
        c = self.config
        previous = np.full(c.fixture_count, c.led_power*c.leds_per_fixture)
        for history in self.patch_histories:
            if not np.isfinite(history).all() or (history < 0).any():
                raise AssertionError('nonfinite or negative reflected optical power')
            energy = history.sum(axis=(0, 1))
            if np.any(energy > previous*c.wall_reflectivity*1.02 + 1e-12):
                raise AssertionError('reflection optical power does not decay as expected')
            previous = energy

    def _receiver_geometry(self, position: Sequence[float]):
        c = self.config
        position = np.asarray(position, dtype=float)
        if position.shape != (3,) or not np.isfinite(position).all():
            raise ValueError('receiver position must be a finite 3-vector')
        width, length, height = c.room
        if abs(position[0]) > width/2 or abs(position[1]) > length/2 or not 0 <= position[2] < height:
            raise ValueError('receiver must lie within room and below the ceiling')
        distance_led = np.linalg.norm(self.led_positions-position, axis=2)
        cos_led = (self.led_positions[:, :, 2]-position[2])/distance_led
        led_gain = ((c.lambertian_order+1)*c.pd_area*c.led_power
                    *c.responsivity*c.concentrator_gain
                    *cos_led**(c.lambertian_order+1)/(2*math.pi*distance_led**2))
        led_gain *= cos_led + 1e-15 >= math.cos(math.radians(c.fov_deg))
        arrival = distance_led/C_LIGHT
        visible = led_gain > 0
        # If no direct path is visible, retain geometric LOS synchronisation.
        origin = float(np.min(arrival[visible])) if visible.any() else float(np.min(arrival))
        delta = position-self.patch_positions
        distance = np.linalg.norm(delta, axis=1)
        with np.errstate(divide='ignore', invalid='ignore'):
            unit = np.divide(delta, distance[:, None], out=np.zeros_like(delta), where=distance[:, None]>0)
            cos_out = np.maximum(np.einsum('pd,pd->p', unit, self.patch_normals), 0)
            cos_in = np.maximum(-unit[:, 2], 0)
            gain = (c.pd_area*cos_out*cos_in/(math.pi*np.maximum(distance, 1e-30)**2)
                    *c.responsivity*c.concentrator_gain)
        gain *= cos_in + 1e-15 >= math.cos(math.radians(c.fov_deg))
        return led_gain, arrival, origin, gain, distance/C_LIGHT

    def _order(self, max_reflections: int | None) -> int:
        order = self.config.max_reflections if max_reflections is None else max_reflections
        if not isinstance(order, (int, np.integer)) or not 0 <= order <= self.config.max_reflections:
            raise ValueError('requested reflection order exceeds precomputed model')
        return int(order)

    def components(self, position: Sequence[float], S: int = 50,
                   max_reflections: int | None = None) -> np.ndarray:
        """Return order-separated matrices of shape (L+1, S, fixtures).

        Taps integrate delayed impulses into [s*Ts,(s+1)*Ts) relative to the
        earliest visible direct path. Unrepresented later energy is truncated,
        not folded into the last tap. Index0 is the useful-symbol interval.
        """
        if not isinstance(S, (int, np.integer)) or not 1 <= S <= 50:
            raise ValueError('S must be an integer from 1 through 50')
        order = self._order(max_reflections)
        return self._cached_components(tuple(float(x) for x in position), int(S), order).copy()

    @lru_cache(maxsize=512)
    def _cached_components(self, position: tuple[float, float, float], S: int, order: int) -> np.ndarray:
        c = self.config
        direct, arrivals, origin, gain, final_delay = self._receiver_geometry(position)
        result = np.zeros((order+1, S, c.fixture_count))
        direct_bins = np.floor(np.maximum(0, arrivals-origin)/c.symbol_period + 1e-12).astype(int)
        for fixture in range(c.fixture_count):
            keep = direct_bins[fixture] < S
            result[0, :, fixture] = np.bincount(direct_bins[fixture, keep],
                weights=direct[fixture, keep], minlength=S)[:S]
        if order:
            delays = self.absolute_times[None, :] + final_delay[:, None]-origin
            # Fractional-time propagation can put tiny interpolation mass before
            # the true first arrival; clamp it to the causal first interval.
            bins = np.floor(np.maximum(delays, 0)/c.symbol_period + 1e-12).astype(int)
            keep = bins < S
            selected_bins = bins[keep]
            for l in range(1, order+1):
                weights = self.patch_histories[l-1]*gain[:, None, None]
                for fixture in range(c.fixture_count):
                    result[l, :, fixture] = np.bincount(selected_bins,
                        weights=weights[:, :, fixture][keep], minlength=S)[:S]
        if not np.isfinite(result).all() or np.any(result < 0):
            raise AssertionError('invalid channel matrix')
        return result

    def matrix(self, position: Sequence[float], S: int = 50,
               max_reflections: int | None = None, first_tap_only: bool = False) -> np.ndarray:
        """Summed electrical impulse-response tap gains, shape (S, fixtures).

        first_tap_only preserves shape and zeros all taps after the first.
        For 'no ISI, retain every optical path', use dc_gain(...)[None, :]
        instead: dropping delayed paths is a different baseline.
        """
        result = self.components(position, S, max_reflections).sum(axis=0)
        if first_tap_only:
            result[1:] = 0
        return result

    def component_dc_gain(self, position: Sequence[float],
                          max_reflections: int | None = None) -> np.ndarray:
        """Return time-integrated gains per reflection order, shape (L+1,F)."""
        order = self._order(max_reflections)
        direct, _, _, gain, _ = self._receiver_geometry(position)
        result = np.zeros((order+1, self.config.fixture_count))
        result[0] = direct.sum(axis=1)
        for l in range(1, order+1):
            result[l] = (self.patch_histories[l-1].sum(axis=1)*gain[:, None]).sum(axis=0)
        return result

    def dc_gain(self, position: Sequence[float], max_reflections: int | None = None) -> np.ndarray:
        return self.component_dc_gain(position, max_reflections).sum(axis=0)

    def metadata(self) -> dict:
        return {
            'config': asdict(self.config),
            'model': 'deterministic centre-element diffuse wall reflection; fractional-delay transport',
            'patches': len(self.patch_positions),
            'time_bins': self.time_count,
            'max_wall_transfer_fraction': self.transition_energy_max,
            'emitted_wall_power_by_order_W': [h.sum(axis=(0, 1)).tolist() for h in self.patch_histories],
            'units': 'A at unit normalised modulation (P_LED and PD responsivity included)',
        }


def self_check() -> dict:
    """Meaningful numerical checks; invoked by `python channel.py`."""
    c = ChannelConfig()
    model = VLCChannel(c)
    bob, eve = (2.0, 0.0, 0.0), (-2.0, 0.0, 0.0)
    HB, HE = model.matrix(bob), model.matrix(eve)
    assert HB.shape == (50, 4) and np.isfinite(HB).all() and (HB >= 0).all()
    assert np.array_equal(HB, model.matrix(bob))
    assert np.allclose(HB[:, [2, 3, 0, 1]], HE, rtol=1e-12, atol=1e-15)
    assert np.allclose(HB.sum(axis=0), model.dc_gain(bob), rtol=1e-10, atol=1e-15)
    assert np.allclose(model.matrix(bob, 1)[0], HB[0])
    direct = model.matrix(bob, max_reflections=0)
    assert np.count_nonzero(direct[1:]) == 0
    expected_single = ((c.lambertian_order+1)*c.pd_area/(2*math.pi*5**2)
                       *c.led_power*c.responsivity*c.concentrator_gain)
    assert math.isclose(los_gain((0, 0, 5), (0, 0, 0), c), expected_single, rel_tol=1e-14)
    by_order = model.component_dc_gain(bob)
    assert (by_order[1:] > 0).all()
    assert (by_order[2:] < by_order[1:-1]).all()
    for l in range(4):
        assert np.all(model.matrix(bob, max_reflections=l+1) >= model.matrix(bob, max_reflections=l))
    first = model.matrix(bob, first_tap_only=True)
    assert np.count_nonzero(first[1:]) == 0 and np.array_equal(first[0], HB[0])
    return {'checks': 11, 'status': 'passed', 'bob_dc_gain_A': model.dc_gain(bob).tolist(),
            'bob_gain_by_order_A': by_order.tolist(),
            'bob_nonzero_taps': int(np.count_nonzero(HB.sum(axis=1))),
            'metadata': model.metadata()}


if __name__ == '__main__':
    print(json.dumps(self_check(), indent=2))
