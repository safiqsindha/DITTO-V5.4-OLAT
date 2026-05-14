#!/usr/bin/env python3
"""
Day 2 Analysis — Project Ditto OLAT
Computes per-condition detection rates, gaps, effect sizes, BCa CIs,
six sensitivity analyses, empirical Bayes shrinkage, and cross-model deltas
across three Lever 24 ground-truth universes.

Outputs (in pre-registration/day_2/):
  completeness_report.json
  effect_table_universe_L1.csv
  effect_table_universe_L2.csv
  effect_table_universe_L3.csv
  cross_model_deltas.csv
  sensitivity_analyses.json
  day_2_summary.md

Usage:
  python3 day2_analysis.py [--check-only] [--universe L1|L2|L3]
"""

import argparse
import csv
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import norm as sp_norm

# ---------------------------------------------------------------------------
# Paths and constants
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PREREGISTRATION = SCRIPT_DIR.parent
PROVENANCE_LOG = PREREGISTRATION / "parser_provenance.ndjson"
ASSIGNMENTS_LOG = PREREGISTRATION / "chain_condition_assignments.ndjson"
DAY2_DIR = PREREGISTRATION / "day_2"

SPEC_HASH = "dbae94dba3ee39d67b131639ae626b1afa7f14645008d37aa0bb464e91980fc8"
N_BOOT = 10_000
SEED_FLASH = 42
SEED_PRO = 43
CI = 0.95
MIN_N_VALID = 25      # suppress CI below this
PARSE_FAIL_WARN = 0.10

UNIVERSES = ['L1', 'L2', 'L3']
UNIVERSE_KEY = {
    'L1': 'L1_shuffled_vs_real',
    'L2': 'L2_planted_violations',
    'L3': 'L3_symbolic_checker',
}
MODELS = ['deepseek-v4-flash', 'deepseek-v4-pro']
MODEL_SEED = {'deepseek-v4-flash': SEED_FLASH, 'deepseek-v4-pro': SEED_PRO}
MODEL_BASELINE = {
    'deepseek-v4-flash': 'flash_baseline',
    'deepseek-v4-pro': 'pro_baseline',
}

MEANINGFUL = 0.10
DIRECTIONAL = 0.03

STAGE_RANK = {'strict': 0, 'permissive': 1, 'md_strip': 2,
              'last_token': 3, 'unparseable': 4, 'api_failure': 5}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def load_ndjson(path):
    records = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


# ---------------------------------------------------------------------------
# Completeness check
# ---------------------------------------------------------------------------
def completeness_check(provenance, assignments):
    prov_keys = {(r['condition_id'], r['sample_id']) for r in provenance}
    assign_keys = {(r['condition_id'], r['chain_id']) for r in assignments}

    prov_only = prov_keys - assign_keys
    assign_only = assign_keys - prov_keys

    cond_prov = Counter(r['condition_id'] for r in provenance)
    cond_assign = Counter(r['condition_id'] for r in assignments)
    wrong_count = {c: {'expected': cond_assign[c], 'found': cond_prov.get(c, 0)}
                   for c in cond_assign if cond_prov.get(c, 0) != cond_assign[c]}

    n_api_fail = sum(1 for r in provenance if r.get('api_failure'))
    n_parse_fail = sum(1 for r in provenance
                       if not r.get('parse_success') and not r.get('api_failure'))
    n_eligible = len(provenance) - n_api_fail

    complete = not prov_only and not assign_only and not wrong_count
    report = {
        'n_provenance': len(provenance),
        'n_assignments': len(assignments),
        'is_complete': complete,
        'n_orphan_prov_only': len(prov_only),
        'n_orphan_assign_only': len(assign_only),
        'orphan_prov_only_sample': sorted(str(k) for k in list(prov_only)[:10]),
        'orphan_assign_only_sample': sorted(str(k) for k in list(assign_only)[:10]),
        'conditions_wrong_count': wrong_count,
        'n_api_failures': n_api_fail,
        'n_parse_failures': n_parse_fail,
        'global_parse_fail_rate': round(n_parse_fail / n_eligible, 4) if n_eligible else None,
    }
    return report, complete


# ---------------------------------------------------------------------------
# Condition data: build aligned numpy arrays per condition
# ---------------------------------------------------------------------------
STAGE_IS_FALLBACK = {
    'md_strip': True, 'last_token': True,
    'strict': False, 'permissive': False,
    'unparseable': False, 'api_failure': False,
}


def build_condition_arrays(provenance, chain_order):
    """
    Group provenance by (model, condition_id). For each group, build arrays
    aligned to chain_order (list of chain_ids, same for all conditions).

    Returns: dict[(model, condition_id)] -> {
        'is_yes': float np.array (1=YES, 0=NO, nan=unparseable),
        'is_api_fail': bool np.array,
        'is_unparseable': bool np.array,
        'is_stage34': bool np.array,  # md_strip or last_token
        'is_violated': dict[universe] -> bool np.array,
        'raw_len': int np.array,
        'lever_varied': int or None,
        'level_varied': str or None,
        'model': str,
        'condition_id': str,
    }
    """
    # Group records by (model, condition_id, chain_id)
    lookup = {}
    for r in provenance:
        key = (r['model'], r['condition_id'], r['sample_id'])
        lookup[key] = r

    # Collect all (model, condition_id) pairs
    cond_keys = set((r['model'], r['condition_id']) for r in provenance)
    result = {}

    for model, cond_id in cond_keys:
        n = len(chain_order)
        is_yes = np.full(n, np.nan)
        is_api_fail = np.zeros(n, dtype=bool)
        is_unparseable = np.zeros(n, dtype=bool)
        is_stage34 = np.zeros(n, dtype=bool)
        is_violated = {u: np.zeros(n, dtype=bool) for u in UNIVERSES}
        raw_len = np.zeros(n, dtype=int)
        lever_varied = None
        level_varied = None

        for i, chain_id in enumerate(chain_order):
            rec = lookup.get((model, cond_id, chain_id))
            if rec is None:
                is_api_fail[i] = True
                continue

            lever_varied = rec.get('lever_varied')
            level_varied = rec.get('level_varied')

            if rec.get('api_failure'):
                is_api_fail[i] = True
                continue

            stage = rec.get('parse_stage_reached', 'unparseable')
            label = rec.get('parsed_label')

            if label == 'YES':
                is_yes[i] = 1.0
            elif label == 'NO':
                is_yes[i] = 0.0
            else:
                is_unparseable[i] = True  # is_yes stays nan

            if stage in ('md_strip', 'last_token'):
                is_stage34[i] = True

            gt = rec.get('ground_truth') or {}
            for u, key in UNIVERSE_KEY.items():
                is_violated[u][i] = bool(gt.get(key, False))

            raw_len[i] = len(rec.get('raw_output') or '')

        result[(model, cond_id)] = {
            'is_yes': is_yes,
            'is_api_fail': is_api_fail,
            'is_unparseable': is_unparseable,
            'is_stage34': is_stage34,
            'is_violated': is_violated,
            'raw_len': raw_len,
            'lever_varied': lever_varied,
            'level_varied': level_varied,
            'model': model,
            'condition_id': cond_id,
        }

    return result


def get_effective_is_yes(cdata, treatment):
    """Return (is_yes_effective, is_valid) for a given treatment."""
    is_api = cdata['is_api_fail']
    is_unp = cdata['is_unparseable']
    raw = cdata['is_yes'].copy()

    if treatment == 'primary':
        is_valid = ~is_api & ~is_unp
        iy = raw
    elif treatment == 'as_no':
        is_valid = ~is_api
        iy = np.where(is_unp, 0.0, raw)
    elif treatment == 'as_random':
        is_valid = ~is_api
        iy = np.where(is_unp, 0.5, raw)
    elif treatment == 'parser_strict':
        is_valid = ~is_api & ~is_unp & ~cdata['is_stage34']
        iy = raw
    else:
        raise ValueError(f"Unknown treatment: {treatment}")

    return iy, is_valid


# ---------------------------------------------------------------------------
# Vectorized gap computation
# ---------------------------------------------------------------------------
def gap_vec(is_yes, is_violated, is_valid):
    """
    Compute gap = dr_violated - dr_intact, all nan-safe.
    All inputs: 1D float/bool arrays of length n.
    Returns (dr_violated, dr_intact, gap, n_violated_valid, n_intact_valid).
    """
    viol_mask = is_violated & is_valid
    int_mask = (~is_violated) & is_valid
    n_v = viol_mask.sum()
    n_i = int_mask.sum()

    iy_safe = np.where(np.isnan(is_yes), 0.0, is_yes)

    dr_v = float(iy_safe[viol_mask].sum() / n_v) if n_v > 0 else np.nan
    dr_i = float(iy_safe[int_mask].sum() / n_i) if n_i > 0 else np.nan
    gap = (dr_v - dr_i) if (not np.isnan(dr_v) and not np.isnan(dr_i)) else np.nan

    return dr_v, dr_i, gap, int(n_v), int(n_i)


def batch_gap(is_yes, is_violated, is_valid, all_idx):
    """
    Vectorized gap for n_boot bootstrap samples.
    all_idx: (n_boot, n) integer array of resampled indices.
    Returns: (n_boot,) float array of gaps.
    """
    iy = is_yes[all_idx]          # (n_boot, n)
    iv = is_violated[all_idx]     # (n_boot, n)
    ivm = is_valid[all_idx]       # (n_boot, n)

    viol = iv & ivm
    intact = (~iv) & ivm

    iy_safe = np.where(np.isnan(iy), 0.0, iy)

    n_v = viol.sum(axis=1)
    n_i = intact.sum(axis=1)

    dr_v = np.where(n_v > 0, (iy_safe * viol).sum(axis=1) / np.maximum(n_v, 1), np.nan)
    dr_i = np.where(n_i > 0, (iy_safe * intact).sum(axis=1) / np.maximum(n_i, 1), np.nan)

    return dr_v - dr_i  # (n_boot,) — nan where either side is empty


# ---------------------------------------------------------------------------
# BCa bootstrap
# ---------------------------------------------------------------------------
def bca_ci(boot_vals, theta_hat, jack_vals):
    """
    Compute BCa CI from pre-computed bootstrap and jackknife distributions.
    Returns (ci_lo, ci_hi, boot_std).
    """
    valid = boot_vals[~np.isnan(boot_vals)]
    if len(valid) < 50:
        return None, None, None

    boot_std = float(np.std(valid, ddof=1))

    # Bias correction z0
    frac_below = np.mean(valid < theta_hat)
    frac_below = np.clip(frac_below, 1e-6, 1 - 1e-6)
    z0 = sp_norm.ppf(frac_below)

    # Acceleration a_hat from jackknife
    jv = jack_vals[~np.isnan(jack_vals)]
    if len(jv) < 3:
        a_hat = 0.0
    else:
        jack_mean = np.mean(jv)
        diff = jack_mean - jv
        num = np.sum(diff**3)
        den = 6.0 * (np.sum(diff**2)**1.5)
        a_hat = float(num / den) if den != 0 else 0.0

    alpha = (1 - CI) / 2

    def adj(a_r):
        z_a = sp_norm.ppf(np.clip(a_r, 1e-8, 1 - 1e-8))
        inner = z0 + (z0 + z_a) / (1 - a_hat * (z0 + z_a))
        return float(sp_norm.cdf(inner))

    lo = float(np.percentile(valid, 100 * adj(alpha)))
    hi = float(np.percentile(valid, 100 * adj(1 - alpha)))
    return lo, hi, boot_std


def bootstrap_effect(cond, base, universe, seed, treatment='primary'):
    """
    BCa bootstrap CI for effect_size = gap(cond) - gap(base).
    Jointly resamples condition and baseline (same indices per iteration).
    Returns (effect_size, ci_lo, ci_hi, boot_std, n_valid_boot).
    """
    iy_c, iv_c = get_effective_is_yes(cond, treatment)
    iy_b, iv_b = get_effective_is_yes(base, treatment)
    ukey = cond['is_violated'][universe]  # same for base (shared chains)

    n = len(iy_c)

    # Point estimates
    _, _, gap_c, _, _ = gap_vec(iy_c, ukey, iv_c)
    _, _, gap_b, _, _ = gap_vec(iy_b, ukey, iv_b)
    if np.isnan(gap_c) or np.isnan(gap_b):
        return np.nan, None, None, None, 0
    theta_hat = float(gap_c - gap_b)

    # Generate all bootstrap indices at once
    rng = np.random.default_rng(seed)
    all_idx = rng.integers(0, n, size=(N_BOOT, n))

    boot_c = batch_gap(iy_c, ukey, iv_c, all_idx)
    boot_b = batch_gap(iy_b, ukey, iv_b, all_idx)
    boot_eff = boot_c - boot_b
    n_valid_boot = int((~np.isnan(boot_eff)).sum())

    # Jackknife (sequential, n=50 — fast enough)
    jack_effs = np.full(n, np.nan)
    for i in range(n):
        idx = np.concatenate([np.arange(i), np.arange(i + 1, n)])
        _, _, gc, _, _ = gap_vec(iy_c[idx], ukey[idx], iv_c[idx])
        _, _, gb, _, _ = gap_vec(iy_b[idx], ukey[idx], iv_b[idx])
        if not np.isnan(gc) and not np.isnan(gb):
            jack_effs[i] = gc - gb

    ci_lo, ci_hi, boot_std = bca_ci(boot_eff, theta_hat, jack_effs)
    return theta_hat, ci_lo, ci_hi, boot_std, n_valid_boot


def bootstrap_gap_only(cdata, universe, seed, treatment='primary'):
    """
    BCa bootstrap CI for the gap of a single condition (used for baseline).
    Returns (gap, ci_lo, ci_hi, boot_std).
    """
    iy, iv = get_effective_is_yes(cdata, treatment)
    ukey = cdata['is_violated'][universe]
    n = len(iy)

    _, _, gap, _, _ = gap_vec(iy, ukey, iv)
    if np.isnan(gap):
        return np.nan, None, None, None

    rng = np.random.default_rng(seed)
    all_idx = rng.integers(0, n, size=(N_BOOT, n))
    boot_gaps = batch_gap(iy, ukey, iv, all_idx)

    jack_gaps = np.full(n, np.nan)
    for i in range(n):
        idx = np.concatenate([np.arange(i), np.arange(i + 1, n)])
        _, _, g, _, _ = gap_vec(iy[idx], ukey[idx], iv[idx])
        jack_gaps[i] = g

    ci_lo, ci_hi, boot_std = bca_ci(boot_gaps, gap, jack_gaps)
    return gap, ci_lo, ci_hi, boot_std


# ---------------------------------------------------------------------------
# Cross-model delta bootstrap (SPEC §9.0)
# Step 1: 10K bootstrap per model (seeds 42/43)
# Step 2: element-wise difference of the two bootstrap distributions → BCa CI
# ---------------------------------------------------------------------------
def bootstrap_cross_model_delta(flash_cond, flash_base, pro_cond, pro_base, universe):
    """
    Returns (delta, ci_lo, ci_hi, boot_std).
    delta = (flash_gap_cond - flash_gap_base) - (pro_gap_cond - pro_gap_base)
    """
    treatment = 'primary'
    ukey_f = flash_cond['is_violated'][universe]
    ukey_p = pro_cond['is_violated'][universe]

    # Flash step 1
    iy_fc, iv_fc = get_effective_is_yes(flash_cond, treatment)
    iy_fb, iv_fb = get_effective_is_yes(flash_base, treatment)
    n_f = len(iy_fc)
    rng_f = np.random.default_rng(SEED_FLASH)
    idx_f = rng_f.integers(0, n_f, size=(N_BOOT, n_f))
    flash_boot = batch_gap(iy_fc, ukey_f, iv_fc, idx_f) - batch_gap(iy_fb, ukey_f, iv_fb, idx_f)

    # Pro step 1
    iy_pc, iv_pc = get_effective_is_yes(pro_cond, treatment)
    iy_pb, iv_pb = get_effective_is_yes(pro_base, treatment)
    n_p = len(iy_pc)
    rng_p = np.random.default_rng(SEED_PRO)
    idx_p = rng_p.integers(0, n_p, size=(N_BOOT, n_p))
    pro_boot = batch_gap(iy_pc, ukey_p, iv_pc, idx_p) - batch_gap(iy_pb, ukey_p, iv_pb, idx_p)

    # Step 2: delta distribution
    delta_boot = flash_boot - pro_boot

    # Point estimate
    _, _, gc_f, _, _ = gap_vec(iy_fc, ukey_f, iv_fc)
    _, _, gb_f, _, _ = gap_vec(iy_fb, ukey_f, iv_fb)
    _, _, gc_p, _, _ = gap_vec(iy_pc, ukey_p, iv_pc)
    _, _, gb_p, _, _ = gap_vec(iy_pb, ukey_p, iv_pb)
    if any(np.isnan(v) for v in (gc_f, gb_f, gc_p, gb_p)):
        return np.nan, None, None, None
    theta_hat = float((gc_f - gb_f) - (gc_p - gb_p))

    # Jackknife for delta: jointly remove chain i from all four sets
    n = n_f
    jack_deltas = np.full(n, np.nan)
    for i in range(n):
        idx = np.concatenate([np.arange(i), np.arange(i + 1, n)])
        _, _, gcf, _, _ = gap_vec(iy_fc[idx], ukey_f[idx], iv_fc[idx])
        _, _, gbf, _, _ = gap_vec(iy_fb[idx], ukey_f[idx], iv_fb[idx])
        _, _, gcp, _, _ = gap_vec(iy_pc[idx], ukey_p[idx], iv_pc[idx])
        _, _, gbp, _, _ = gap_vec(iy_pb[idx], ukey_p[idx], iv_pb[idx])
        if not any(np.isnan(v) for v in (gcf, gbf, gcp, gbp)):
            jack_deltas[i] = (gcf - gbf) - (gcp - gbp)

    ci_lo, ci_hi, boot_std = bca_ci(delta_boot, theta_hat, jack_deltas)
    return theta_hat, ci_lo, ci_hi, boot_std


# ---------------------------------------------------------------------------
# Classification (SPEC §9, Amendment #4 C5)
# ---------------------------------------------------------------------------
def classify(effect, ci_lo, ci_hi):
    """
    Returns (classification_str, ci_excludes_zero).
    """
    if effect is None or np.isnan(effect):
        return 'Unknown', None

    abs_eff = abs(effect)
    if abs_eff < DIRECTIONAL:
        return 'Null', None

    # CI check
    ci_ok = ci_lo is not None and ci_hi is not None
    if ci_ok:
        # excludes zero on the correct side
        excludes = (effect > 0 and ci_lo > 0) or (effect < 0 and ci_hi < 0)
    else:
        excludes = None

    if abs_eff >= MEANINGFUL:
        candidate = 'Meaningful'
    else:
        candidate = 'Directional'

    if not ci_ok or excludes is None:
        return f'{candidate}(no_CI)', None
    if excludes:
        return candidate, True
    else:
        # Downgrade one level
        return ('Directional' if candidate == 'Meaningful' else 'Null'), False


# ---------------------------------------------------------------------------
# Cohen's h
# ---------------------------------------------------------------------------
def cohens_h(p1, p2):
    if p1 is None or np.isnan(p1) or p2 is None or np.isnan(p2):
        return np.nan
    p1 = max(0.0, min(1.0, p1))
    p2 = max(0.0, min(1.0, p2))
    return 2 * math.asin(math.sqrt(p1)) - 2 * math.asin(math.sqrt(p2))


# ---------------------------------------------------------------------------
# Arcsine sensitivity (SPEC §9.2 S3, method=arcsine, locked per E3)
# ---------------------------------------------------------------------------
def arcsine_effect(cdata, bdata, universe):
    iy_c, iv_c = get_effective_is_yes(cdata, 'primary')
    iy_b, iv_b = get_effective_is_yes(bdata, 'primary')
    ukey = cdata['is_violated'][universe]

    dr_vc, dr_ic, _, _, _ = gap_vec(iy_c, ukey, iv_c)
    dr_vb, dr_ib, _, _, _ = gap_vec(iy_b, ukey, iv_b)

    def arc_gap(dr_v, dr_i):
        if np.isnan(dr_v) or np.isnan(dr_i):
            return np.nan
        av = 2 * math.asin(math.sqrt(max(0, min(1, dr_v))))
        ai = 2 * math.asin(math.sqrt(max(0, min(1, dr_i))))
        return av - ai

    ag_c = arc_gap(dr_vc, dr_ic)
    ag_b = arc_gap(dr_vb, dr_ib)
    eff = (ag_c - ag_b) if (not np.isnan(ag_c) and not np.isnan(ag_b)) else np.nan
    return float(eff), float(ag_c), float(ag_b)


# ---------------------------------------------------------------------------
# Sensitivity S6: L18 L2/L3 response-length quartile analysis
# ---------------------------------------------------------------------------
def sensitivity_l18_quartile(cdata, universe):
    iy, iv = get_effective_is_yes(cdata, 'primary')
    ukey = cdata['is_violated'][universe]
    valid_mask = ~cdata['is_api_fail'] & ~cdata['is_unparseable']

    valid_idx = np.where(valid_mask)[0]
    if len(valid_idx) < 8:
        return {'n_valid': int(len(valid_idx)), 'note': 'insufficient_n'}

    lengths = cdata['raw_len'][valid_idx]
    quartile_boundaries = np.percentile(lengths, [25, 50, 75]).tolist()
    bins = np.digitize(lengths, quartile_boundaries)  # 0=Q1 ... 3=Q4

    quartile_gaps = {}
    for q in range(4):
        q_idx = valid_idx[bins == q]
        if len(q_idx) < 3:
            quartile_gaps[f'Q{q + 1}'] = None
            continue
        _, _, gap, _, _ = gap_vec(iy[q_idx], ukey[q_idx], iv[q_idx])
        quartile_gaps[f'Q{q + 1}'] = None if np.isnan(gap) else float(gap)

    return {
        'n_valid': int(len(valid_idx)),
        'quartile_boundaries': quartile_boundaries,
        'quartile_gaps': quartile_gaps,
    }


# ---------------------------------------------------------------------------
# Empirical Bayes shrinkage
# SPEC §9.1: prior mean=0, prior variance=median observed variance across levers
# ---------------------------------------------------------------------------
def eb_shrink(effect_sizes, boot_stds):
    """
    Returns list of shrunken effect sizes.
    effect_sizes, boot_stds: lists (NaN-safe).
    """
    pairs = [(e, s) for e, s in zip(effect_sizes, boot_stds)
             if e is not None and s is not None
             and not np.isnan(e) and not np.isnan(s) and s > 0]
    if len(pairs) < 2:
        return list(effect_sizes)

    ses2 = np.array([p[1]**2 for p in pairs])
    tau2 = float(np.median(ses2))  # prior variance = median observed variance

    shrunken = []
    pair_idx = 0
    for e, s in zip(effect_sizes, boot_stds):
        if e is None or s is None or np.isnan(e) or np.isnan(s) or s <= 0:
            shrunken.append(e)
        else:
            se2 = ses2[pair_idx]
            B = se2 / (se2 + tau2) if tau2 > 0 else 1.0
            # prior mean = 0 → shrunken = 0 + (1 - B) * e
            shrunken.append(float((1 - B) * e))
            pair_idx += 1
    return shrunken


# ---------------------------------------------------------------------------
# Main analysis: compute all rows for one universe
# ---------------------------------------------------------------------------
def analyze_universe(universe, cond_arrays, chain_order):
    """
    Returns list of result dicts (one per model × condition).
    """
    ukey = UNIVERSE_KEY[universe]
    rows = []

    for model in MODELS:
        seed = MODEL_SEED[model]
        base_id = MODEL_BASELINE[model]
        base_key = (model, base_id)

        if base_key not in cond_arrays:
            print(f"  [WARN] Baseline not found for {model}. Skipping model.")
            continue

        base = cond_arrays[base_key]
        iy_b, iv_b = get_effective_is_yes(base, 'primary')
        uv_b = base['is_violated'][universe]

        model_conds = [(k, v) for k, v in cond_arrays.items() if k[0] == model]
        print(f"  {model}: {len(model_conds)} conditions...")

        for (m, cond_id), cdata in sorted(model_conds, key=lambda x: x[0][1]):
            lever = cdata['lever_varied']
            level = cdata['level_varied']
            is_l18_cot = (lever == 18 and level in ('L2', 'L3'))
            is_baseline = (cond_id == base_id)

            # Core metrics (primary treatment)
            iy_c, iv_c = get_effective_is_yes(cdata, 'primary')
            uv_c = cdata['is_violated'][universe]

            dr_v, dr_i, gap_c, n_viol, n_int = gap_vec(iy_c, uv_c, iv_c)
            _, _, gap_b, _, _ = gap_vec(iy_b, uv_b, iv_b)

            n_total = len(iy_c)
            n_api_fail = int(cdata['is_api_fail'].sum())
            n_unp = int(cdata['is_unparseable'].sum())
            n_valid = n_total - n_api_fail - n_unp
            parse_fail_rate = n_unp / max(n_total - n_api_fail, 1)
            api_fail_rate = n_api_fail / n_total

            degenerate_var = (n_valid > 0) and (
                np.isnan(dr_v) or np.isnan(dr_i) or
                (dr_v == dr_i) or
                (not np.isnan(dr_v) and dr_v in (0.0, 1.0) and
                 not np.isnan(dr_i) and dr_i in (0.0, 1.0))
            )
            insufficient_n = (n_valid < MIN_N_VALID)

            # Effect size + BCa CI
            if is_baseline:
                # For baseline, effect_size = 0 by construction
                effect_size = 0.0
                gap_ci_lo, gap_ci_hi, gap_boot_std = bootstrap_gap_only(
                    cdata, universe, seed)[1:]
                eff_ci_lo, eff_ci_hi, eff_boot_std = None, None, 0.0
            else:
                effect_size, eff_ci_lo, eff_ci_hi, eff_boot_std, _ = bootstrap_effect(
                    cdata, base, universe, seed)
                gap_ci_lo, gap_ci_hi, gap_boot_std = bootstrap_gap_only(
                    cdata, universe, seed)[1:]

            # Suppress CI if insufficient_n or degenerate
            if insufficient_n or degenerate_var:
                eff_ci_lo = eff_ci_hi = None

            classification, ci_excl = classify(effect_size, eff_ci_lo, eff_ci_hi)

            # Sensitivity 1 (as_no)
            s1_eff, s1_ci_lo, s1_ci_hi, _, _ = bootstrap_effect(cdata, base, universe, seed, 'as_no')
            s1_cls, _ = classify(s1_eff, s1_ci_lo, s1_ci_hi)

            # Sensitivity 2 (as_random)
            s2_eff, s2_ci_lo, s2_ci_hi, _, _ = bootstrap_effect(cdata, base, universe, seed, 'as_random')
            s2_cls, _ = classify(s2_eff, s2_ci_lo, s2_ci_hi)

            # Sensitivity 3 (arcsine)
            s3_eff, s3_arc_gap_c, s3_arc_gap_b = arcsine_effect(cdata, base, universe)
            s3_cls, _ = classify(s3_eff, None, None)  # no CI for arcsine sensitivity

            # Sensitivity 4 (parser_strict)
            s4_eff, s4_ci_lo, s4_ci_hi, _, _ = bootstrap_effect(cdata, base, universe, seed, 'parser_strict')
            s4_cls, _ = classify(s4_eff, s4_ci_lo, s4_ci_hi)

            # Sensitivity 5 (parse failure audit)
            s5_flagged = parse_fail_rate > PARSE_FAIL_WARN

            # Sensitivity 6 (L18 L2/L3 quartile)
            s6 = sensitivity_l18_quartile(cdata, universe) if is_l18_cot else None

            # Robustness flags (SPEC §9.2 Amendment #4 B3): count S1-S4 conflicts
            sensitivity_classifications = [s1_cls, s2_cls, s3_cls, s4_cls]
            if 'Null' in classification:
                n_meaningful_sens = sum(1 for c in sensitivity_classifications
                                        if 'Meaningful' in c)
                hidden_signal = n_meaningful_sens >= 3
                robustness_concern = False
            elif 'Meaningful' in classification:
                n_null_sens = sum(1 for c in sensitivity_classifications if 'Null' in c)
                robustness_concern = n_null_sens >= 3
                hidden_signal = False
            else:
                robustness_concern = hidden_signal = False

            # Parse stage distribution
            stages = Counter()
            for r in [cdata]:
                pass  # stages computed from raw_len proxy not available here
            # We'll count from the provenance arrays
            n_strict = int((~cdata['is_api_fail'] & ~cdata['is_unparseable'] &
                            ~cdata['is_stage34']).sum())
            n_fallback = int((~cdata['is_api_fail'] & ~cdata['is_unparseable'] &
                              cdata['is_stage34']).sum())

            row = {
                'condition_id': cond_id,
                'model': model,
                'universe': universe,
                'lever_varied': lever,
                'level_varied': level,
                'is_baseline': is_baseline,
                # Counts
                'n_total': n_total,
                'n_valid': n_valid,
                'n_api_fail': n_api_fail,
                'n_violated_valid': n_viol,
                'n_intact_valid': n_int,
                # Rates
                'dr_violated': None if np.isnan(dr_v) else round(float(dr_v), 4),
                'dr_intact': None if np.isnan(dr_i) else round(float(dr_i), 4),
                'gap': None if np.isnan(gap_c) else round(float(gap_c), 4),
                'gap_ci_lo': round(gap_ci_lo, 4) if gap_ci_lo is not None else None,
                'gap_ci_hi': round(gap_ci_hi, 4) if gap_ci_hi is not None else None,
                # Effect size
                'effect_size': None if (effect_size is None or np.isnan(effect_size)) else round(float(effect_size), 4),
                'effect_ci_lo': round(eff_ci_lo, 4) if eff_ci_lo is not None else None,
                'effect_ci_hi': round(eff_ci_hi, 4) if eff_ci_hi is not None else None,
                'effect_boot_std': round(float(eff_boot_std), 4) if eff_boot_std is not None else None,
                # Classification
                'classification': classification,
                'ci_excludes_zero': ci_excl,
                # Cohen's h
                'cohens_h': round(cohens_h(dr_v, dr_i), 4) if not (np.isnan(dr_v) or np.isnan(dr_i)) else None,
                # Flags
                'parse_failure_rate': round(parse_fail_rate, 4),
                'api_failure_rate': round(api_fail_rate, 4),
                'degenerate_variance': degenerate_var,
                'insufficient_n': insufficient_n,
                'n_parsed_strict12': n_strict,
                'n_parsed_fallback34': n_fallback,
                # Sensitivities
                's1_as_no_effect': None if (s1_eff is None or np.isnan(s1_eff)) else round(float(s1_eff), 4),
                's1_classification': s1_cls,
                's2_as_random_effect': None if (s2_eff is None or np.isnan(s2_eff)) else round(float(s2_eff), 4),
                's2_classification': s2_cls,
                's3_arcsine_effect': None if (s3_eff is None or np.isnan(s3_eff)) else round(float(s3_eff), 4),
                's3_arcsine_gap_cond': None if np.isnan(s3_arc_gap_c) else round(float(s3_arc_gap_c), 4),
                's3_arcsine_gap_base': None if np.isnan(s3_arc_gap_b) else round(float(s3_arc_gap_b), 4),
                's3_classification': s3_cls,
                's4_parser_strict_effect': None if (s4_eff is None or np.isnan(s4_eff)) else round(float(s4_eff), 4),
                's4_ci_lo': round(s4_ci_lo, 4) if s4_ci_lo is not None else None,
                's4_ci_hi': round(s4_ci_hi, 4) if s4_ci_hi is not None else None,
                's4_classification': s4_cls,
                's5_parse_fail_flagged': s5_flagged,
                's6_quartile_analysis': json.dumps(s6) if s6 else None,
                # Robustness
                'robustness_concern': robustness_concern,
                'hidden_signal_candidate': hidden_signal,
            }
            rows.append(row)

    return rows


# ---------------------------------------------------------------------------
# Apply empirical Bayes shrinkage to rows (per model, per universe)
# ---------------------------------------------------------------------------
def apply_eb_shrinkage(rows):
    for model in MODELS:
        for universe in UNIVERSES:
            subset = [r for r in rows
                      if r['model'] == model and r['universe'] == universe
                      and not r['is_baseline']
                      and r['effect_size'] is not None
                      and r['effect_boot_std'] is not None]
            if not subset:
                continue

            effects = [r['effect_size'] for r in subset]
            stds = [r['effect_boot_std'] for r in subset]
            shrunken = eb_shrink(effects, stds)

            for r, s in zip(subset, shrunken):
                r['effect_size_shrunken'] = round(float(s), 4) if s is not None else None

    # Fill None for rows without shrinkage
    for r in rows:
        if 'effect_size_shrunken' not in r:
            r['effect_size_shrunken'] = None
    return rows


# ---------------------------------------------------------------------------
# Cross-model delta table
# ---------------------------------------------------------------------------
def compute_cross_model_deltas(cond_arrays):
    rows = []
    flash_base = cond_arrays.get(('deepseek-v4-flash', 'flash_baseline'))
    pro_base = cond_arrays.get(('deepseek-v4-pro', 'pro_baseline'))
    if flash_base is None or pro_base is None:
        print("  [WARN] Baselines missing for cross-model delta computation")
        return rows

    # Find paired conditions: flash_XXX / pro_XXX with same lever+level
    flash_conds = {k: v for k, v in cond_arrays.items() if k[0] == 'deepseek-v4-flash'
                   and k[1] != 'flash_baseline'}
    pro_conds = {k: v for k, v in cond_arrays.items() if k[0] == 'deepseek-v4-pro'
                 and k[1] != 'pro_baseline'}

    # Match by (lever_varied, level_varied)
    flash_by_ll = {(v['lever_varied'], v['level_varied']): v for v in flash_conds.values()}
    pro_by_ll = {(v['lever_varied'], v['level_varied']): v for v in pro_conds.values()}

    for ll_key in sorted(set(flash_by_ll) & set(pro_by_ll)):
        lever, level = ll_key
        fcond = flash_by_ll[ll_key]
        pcond = pro_by_ll[ll_key]

        print(f"    delta: Lever {lever} {level}...")
        for universe in UNIVERSES:
            delta, ci_lo, ci_hi, boot_std = bootstrap_cross_model_delta(
                fcond, flash_base, pcond, pro_base, universe)
            cls, ci_excl = classify(delta, ci_lo, ci_hi)
            rows.append({
                'universe': universe,
                'lever_varied': lever,
                'level_varied': level,
                'flash_condition_id': fcond['condition_id'],
                'pro_condition_id': pcond['condition_id'],
                'delta_effect': None if (delta is None or np.isnan(delta)) else round(float(delta), 4),
                'delta_ci_lo': round(ci_lo, 4) if ci_lo is not None else None,
                'delta_ci_hi': round(ci_hi, 4) if ci_hi is not None else None,
                'delta_boot_std': round(float(boot_std), 4) if boot_std is not None else None,
                'delta_classification': cls,
                'ci_excludes_zero': ci_excl,
            })
    return rows


# ---------------------------------------------------------------------------
# Write outputs
# ---------------------------------------------------------------------------
def write_csv(rows, path, fieldnames=None):
    if not rows:
        print(f"  [WARN] No rows to write for {path.name}")
        return
    if fieldnames is None:
        fieldnames = list(rows[0].keys())
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)
    print(f"  Wrote {len(rows)} rows → {path.name}")


def write_summary_md(effect_rows, delta_rows, completeness, path):
    lines = [
        "# Day 2 Analysis Summary — Project Ditto OLAT",
        f"\n**SPEC hash:** `{SPEC_HASH}`\n",
        "## Completeness\n",
        f"- Provenance records: {completeness['n_provenance']}",
        f"- Assignments: {completeness['n_assignments']}",
        f"- Complete: {'YES' if completeness['is_complete'] else 'NO — see completeness_report.json'}",
        f"- API failures: {completeness['n_api_failures']}",
        f"- Parse failures: {completeness['n_parse_failures']}",
        f"- Global parse fail rate: {completeness['global_parse_fail_rate']}",
        "\n## Effect Table Summary (Universe L3 — symbolic checker as truth)\n",
    ]

    l3_rows = [r for r in effect_rows if r['universe'] == 'L3' and not r.get('is_baseline')]
    meaningful = [r for r in l3_rows if 'Meaningful' in str(r.get('classification', ''))]
    directional = [r for r in l3_rows if r.get('classification') == 'Directional']
    null = [r for r in l3_rows if r.get('classification') == 'Null']

    lines += [
        f"- Meaningful: {len(meaningful)}",
        f"- Directional: {len(directional)}",
        f"- Null: {len(null)}",
        f"- Total non-baseline conditions: {len(l3_rows)}",
    ]

    if meaningful:
        lines.append("\n### Top Meaningful Effects (sorted by |effect_size|)\n")
        top = sorted(meaningful, key=lambda r: abs(r.get('effect_size') or 0), reverse=True)[:10]
        lines.append("| Condition | Model | Effect | CI | Classification |")
        lines.append("|---|---|---|---|---|")
        for r in top:
            eff = r.get('effect_size')
            lo = r.get('effect_ci_lo')
            hi = r.get('effect_ci_hi')
            ci_str = f"[{lo}, {hi}]" if lo is not None else "—"
            lines.append(f"| {r['condition_id']} | {r['model']} | {eff} | {ci_str} | {r['classification']} |")

    lines.append("\n## Cross-Model Deltas (Universe L3)\n")
    l3_deltas = [r for r in delta_rows if r['universe'] == 'L3']
    m_deltas = [r for r in l3_deltas if 'Meaningful' in str(r.get('delta_classification', ''))]
    lines += [
        f"- Meaningful deltas (Flash vs Pro): {len(m_deltas)} / {len(l3_deltas)}",
    ]

    lines.append("\n## Robustness Flags\n")
    rc = [r for r in l3_rows if r.get('robustness_concern')]
    hs = [r for r in l3_rows if r.get('hidden_signal_candidate')]
    lines += [
        f"- robustness_concern flagged: {len(rc)} conditions" + (f" — {[r['condition_id'] for r in rc]}" if rc else ""),
        f"- hidden_signal_candidate flagged: {len(hs)} conditions" + (f" — {[r['condition_id'] for r in hs]}" if hs else ""),
    ]

    path.write_text('\n'.join(lines) + '\n')
    print(f"  Wrote summary → {path.name}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description='Day 2 Analysis — Project Ditto OLAT')
    parser.add_argument('--check-only', action='store_true',
                        help='Run completeness check only, then exit.')
    parser.add_argument('--universe', choices=UNIVERSES,
                        help='Run analysis for one universe only.')
    args = parser.parse_args()

    DAY2_DIR.mkdir(exist_ok=True)

    # Load data
    print("Loading provenance log...")
    if not PROVENANCE_LOG.exists():
        print(f"ERROR: {PROVENANCE_LOG} not found. Run day1_executor.py first.")
        sys.exit(1)
    provenance = load_ndjson(PROVENANCE_LOG)
    print(f"  {len(provenance)} provenance records")

    print("Loading assignment log...")
    assignments = load_ndjson(ASSIGNMENTS_LOG)
    print(f"  {len(assignments)} assignment records")

    # Completeness check
    print("\nRunning completeness check...")
    comp_report, is_complete = completeness_check(provenance, assignments)

    outpath = DAY2_DIR / 'completeness_report.json'
    outpath.write_text(json.dumps(comp_report, indent=2))
    print(f"  Complete: {comp_report['is_complete']}")
    print(f"  n_provenance={comp_report['n_provenance']}  n_assignments={comp_report['n_assignments']}")
    print(f"  API failures={comp_report['n_api_failures']}  parse failures={comp_report['n_parse_failures']}")

    if args.check_only:
        print("\n--check-only: done.")
        return

    if not comp_report['is_complete']:
        print("\n[WARN] Completeness check failed. Proceeding anyway — results may be incomplete.")

    # Build aligned chain order (union of all chain_ids in provenance)
    all_chain_ids = sorted(set(r['sample_id'] for r in provenance))
    print(f"\nChain order: {len(all_chain_ids)} unique chain IDs")

    # Build condition arrays
    print("Building condition arrays...")
    cond_arrays = build_condition_arrays(provenance, all_chain_ids)
    print(f"  {len(cond_arrays)} (model, condition_id) pairs loaded")

    # Determine universes to run
    universes_to_run = [args.universe] if args.universe else UNIVERSES

    # Analyze each universe
    all_effect_rows = []
    for universe in universes_to_run:
        print(f"\n=== Universe {universe} ({UNIVERSE_KEY[universe]}) ===")
        rows = analyze_universe(universe, cond_arrays, all_chain_ids)
        all_effect_rows.extend(rows)

    # Apply empirical Bayes shrinkage
    print("\nApplying empirical Bayes shrinkage...")
    all_effect_rows = apply_eb_shrinkage(all_effect_rows)

    # Write effect tables (one CSV per universe)
    print("\nWriting effect tables...")
    for universe in universes_to_run:
        u_rows = sorted(
            [r for r in all_effect_rows if r['universe'] == universe],
            key=lambda r: (r['model'], str(r.get('lever_varied', '')), str(r.get('level_varied', '')))
        )
        write_csv(u_rows, DAY2_DIR / f'effect_table_universe_{universe}.csv')

    # Cross-model deltas
    print("\nComputing cross-model deltas...")
    delta_rows = compute_cross_model_deltas(cond_arrays)
    if delta_rows:
        delta_rows_out = [r for r in delta_rows if r['universe'] in universes_to_run]
        write_csv(delta_rows_out, DAY2_DIR / 'cross_model_deltas.csv')

    # Sensitivity summary JSON
    print("\nWriting sensitivity summary...")
    sens_summary = {}
    for r in all_effect_rows:
        key = f"{r['condition_id']}_{r['universe']}"
        sens_summary[key] = {
            'condition_id': r['condition_id'],
            'model': r['model'],
            'universe': r['universe'],
            'primary_classification': r['classification'],
            's1_as_no': {'effect': r['s1_as_no_effect'], 'classification': r['s1_classification']},
            's2_as_random': {'effect': r['s2_as_random_effect'], 'classification': r['s2_classification']},
            's3_arcsine': {'effect': r['s3_arcsine_effect'], 'classification': r['s3_classification']},
            's4_parser_strict': {'effect': r['s4_parser_strict_effect'], 'classification': r['s4_classification']},
            's5_parse_fail_flagged': r['s5_parse_fail_flagged'],
            's6_quartile': r['s6_quartile_analysis'],
            'robustness_concern': r['robustness_concern'],
            'hidden_signal_candidate': r['hidden_signal_candidate'],
        }
    (DAY2_DIR / 'sensitivity_analyses.json').write_text(json.dumps(sens_summary, indent=2))
    print(f"  Wrote {len(sens_summary)} entries → sensitivity_analyses.json")

    # Summary markdown
    write_summary_md(all_effect_rows, delta_rows, comp_report, DAY2_DIR / 'day_2_summary.md')

    print("\n=== Day 2 Analysis Complete ===")
    print(f"  Outputs in: {DAY2_DIR}")


if __name__ == '__main__':
    main()
