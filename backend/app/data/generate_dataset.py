"""
MULESHIELD — Synthetic mule-account dataset generator.

Produces ~8 000 bank-account profiles with 30 behavioural / transactional
features and a binary label ``is_mule``.

Design goals
────────────
• Realistic marginals — each feature uses a domain-appropriate distribution
  (log-normal for amounts, Poisson for counts, Beta for ratios, …).
• Class overlap — mule accounts are *biased* toward suspicious patterns but
  NOT perfectly separable from normal accounts:
    – ~15 % of mules are "near-miss" (look almost normal).
    – ~5 % of normal accounts have 1–2 elevated features (FP-realistic).
• Reproducible via ``seed`` parameter.

The 30 features are grouped into six thematic clusters; see features.md for
the full data-dictionary.

───────────────────────────────────────────────────────────────────────────
FEATURE LIST (12 user-specified + 18 chosen)
───────────────────────────────────────────────────────────────────────────
 #  Feature                           Source
 ── ──────────────────────────────── ──────────
  1 account_age_days                  user
  2 tx_count_30d                      user
  3 unique_remitters_30d              user
  4 unique_beneficiaries_30d          user
  5 rapid_inout_ratio                 user
  6 cash_deposit_ratio                user
  7 night_tx_ratio                    user
  8 device_change_count_30d           user
  9 avg_tx_amount                     user
 10 tx_amount_std                     user
 11 kyc_complete                      user (bool)
 12 login_frequency_30d               user

 ─── 18 additional features (chosen for fraud-relevance) ───
 13 failed_login_count_30d            credential-stuffing / account take-over
 14 international_tx_ratio            cross-border layering
 15 dormancy_before_activity_days     wake-up pattern typical of dormant mules
 16 avg_time_between_tx_hours         rapid cycling vs. organic spacing
 17 max_single_tx_amount              outlier large transfers
 18 round_amount_ratio                structuring / smurfing
 19 same_day_inout_count              pass-through behaviour
 20 weekend_tx_ratio                  unusual timing
 21 atm_withdrawal_ratio              cash-out behaviour
 22 ip_change_count_30d               geo-anomaly / VPN usage
 23 peer_to_peer_tx_ratio             P2P layering
 24 declined_tx_ratio                 probing / testing
 25 multi_currency_flag               cross-currency layering (bool)
 26 avg_balance_30d                   abnormally low for throughput
 27 balance_velocity                  rapid balance swings
 28 linked_accounts_count             nominee networks
 29 phone_change_flag                 SIM-swap / contact change (bool)
 30 email_domain_freemail             free-mail provider for KYC evasion (bool)
───────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import pathlib
from typing import Optional

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
#  Helper: clamp values into a plausible range
# ---------------------------------------------------------------------------
def _clip(arr: np.ndarray, lo: float, hi: float) -> np.ndarray:
    return np.clip(arr, lo, hi)


# ---------------------------------------------------------------------------
#  Core generator
# ---------------------------------------------------------------------------
def generate_dataset(
    n: int = 8_000,
    mule_rate: float = 0.009,
    seed: int = 42,
) -> pd.DataFrame:
    """Return a DataFrame with *n* synthetic bank-account profiles.

    Parameters
    ----------
    n : int
        Total number of accounts.
    mule_rate : float
        Approximate fraction of accounts labelled ``is_mule = 1``.
    seed : int
        Random-number seed for full reproducibility.

    Returns
    -------
    pd.DataFrame   (n rows × 31 columns — 30 features + ``is_mule`` label)
    """
    rng = np.random.default_rng(seed)

    n_mules = int(round(n * mule_rate))
    n_normal = n - n_mules

    # ── assign labels ─────────────────────────────────────────────────
    labels = np.array([0] * n_normal + [1] * n_mules)
    is_mule = labels.astype(bool)

    # ── sub-populations for noise injection ───────────────────────────
    # ~15 % of mules → "near-miss" (distributions almost identical to normal)
    near_miss_mask = np.zeros(n, dtype=bool)
    n_near_miss = max(1, int(round(n_mules * 0.15)))
    mule_indices = np.where(is_mule)[0]
    near_miss_idx = rng.choice(mule_indices, size=n_near_miss, replace=False)
    near_miss_mask[near_miss_idx] = True

    # ~5 % of normal accounts → "FP-noisy" (1–2 features pushed up)
    fp_noisy_mask = np.zeros(n, dtype=bool)
    normal_indices = np.where(~is_mule)[0]
    n_fp = max(1, int(round(n_normal * 0.05)))
    fp_idx = rng.choice(normal_indices, size=n_fp, replace=False)
    fp_noisy_mask[fp_idx] = True

    # ── helper closures ──────────────────────────────────────────────
    def _base(
        normal_loc: float,
        normal_scale: float,
        mule_loc: float,
        mule_scale: float,
        lo: float = 0.0,
        hi: float = np.inf,
        dist: str = "normal",
    ) -> np.ndarray:
        """Sample from two shifted distributions depending on label.

        Near-miss mules use the *normal* parameters.
        """
        arr = np.empty(n, dtype=np.float64)

        # — normal accounts —
        if dist == "lognormal":
            arr[~is_mule] = rng.lognormal(normal_loc, normal_scale, n_normal)
        elif dist == "poisson":
            arr[~is_mule] = rng.poisson(normal_loc, n_normal).astype(float)
        else:
            arr[~is_mule] = rng.normal(normal_loc, normal_scale, n_normal)

        # — mule accounts (full signal) —
        mule_full = mule_indices[~near_miss_mask[mule_indices]]
        mule_nm = mule_indices[near_miss_mask[mule_indices]]
        n_full = len(mule_full)
        n_nm = len(mule_nm)

        if dist == "lognormal":
            arr[mule_full] = rng.lognormal(mule_loc, mule_scale, n_full)
            arr[mule_nm] = rng.lognormal(normal_loc, normal_scale, n_nm)
        elif dist == "poisson":
            arr[mule_full] = rng.poisson(mule_loc, n_full).astype(float)
            arr[mule_nm] = rng.poisson(normal_loc, n_nm).astype(float)
        else:
            arr[mule_full] = rng.normal(mule_loc, mule_scale, n_full)
            arr[mule_nm] = rng.normal(normal_loc, normal_scale, n_nm)

        return _clip(arr, lo, hi)

    def _ratio(
        normal_loc: float,
        normal_scale: float,
        mule_loc: float,
        mule_scale: float,
    ) -> np.ndarray:
        """Beta-ish ratio ∈ [0, 1]."""
        return _base(normal_loc, normal_scale, mule_loc, mule_scale, 0.0, 1.0)

    # ==================================================================
    #  Generate each feature with domain-appropriate distributions
    # ==================================================================

    data: dict[str, np.ndarray] = {}

    # 1. account_age_days — normal accounts: older; mules: newer
    data["account_age_days"] = _base(
        normal_loc=1100, normal_scale=600,
        mule_loc=120, mule_scale=80,
        lo=7, hi=7300,
    )

    # 2. tx_count_30d — Poisson counts
    data["tx_count_30d"] = _base(
        normal_loc=15, normal_scale=0,
        mule_loc=80, mule_scale=0,
        lo=0, hi=500, dist="poisson",
    )

    # 3. unique_remitters_30d
    data["unique_remitters_30d"] = _base(
        normal_loc=3, normal_scale=0,
        mule_loc=18, mule_scale=0,
        lo=0, hi=200, dist="poisson",
    )

    # 4. unique_beneficiaries_30d
    data["unique_beneficiaries_30d"] = _base(
        normal_loc=4, normal_scale=0,
        mule_loc=22, mule_scale=0,
        lo=0, hi=200, dist="poisson",
    )

    # 5. rapid_inout_ratio (ratio)
    data["rapid_inout_ratio"] = _ratio(0.05, 0.04, 0.55, 0.18)

    # 6. cash_deposit_ratio
    data["cash_deposit_ratio"] = _ratio(0.10, 0.08, 0.50, 0.15)

    # 7. night_tx_ratio
    data["night_tx_ratio"] = _ratio(0.08, 0.06, 0.35, 0.12)

    # 8. device_change_count_30d
    data["device_change_count_30d"] = _base(
        normal_loc=0.5, normal_scale=0,
        mule_loc=4, mule_scale=0,
        lo=0, hi=30, dist="poisson",
    )

    # 9. avg_tx_amount (log-normal for realistic heavy tail)
    data["avg_tx_amount"] = _base(
        normal_loc=6.5, normal_scale=1.2,
        mule_loc=8.2, mule_scale=0.9,
        lo=1, hi=500_000, dist="lognormal",
    )

    # 10. tx_amount_std (log-normal)
    data["tx_amount_std"] = _base(
        normal_loc=5.5, normal_scale=1.4,
        mule_loc=7.8, mule_scale=1.0,
        lo=0, hi=500_000, dist="lognormal",
    )

    # 11. kyc_complete (boolean — most normal accounts complete KYC)
    kyc = np.ones(n, dtype=np.int8)
    kyc[~is_mule] = rng.choice([0, 1], size=n_normal, p=[0.03, 0.97])
    # mule accounts: ~30 % incomplete KYC (full signal), near-miss → normal
    kyc[mule_indices[~near_miss_mask[mule_indices]]] = rng.choice(
        [0, 1],
        size=len(mule_indices[~near_miss_mask[mule_indices]]),
        p=[0.30, 0.70],
    )
    kyc[mule_indices[near_miss_mask[mule_indices]]] = rng.choice(
        [0, 1],
        size=len(mule_indices[near_miss_mask[mule_indices]]),
        p=[0.03, 0.97],
    )
    data["kyc_complete"] = kyc

    # 12. login_frequency_30d
    data["login_frequency_30d"] = _base(
        normal_loc=18, normal_scale=10,
        mule_loc=55, mule_scale=20,
        lo=0, hi=300,
    )

    # ────────────────── Additional 18 features ──────────────────

    # 13. failed_login_count_30d
    data["failed_login_count_30d"] = _base(
        normal_loc=0.8, normal_scale=0,
        mule_loc=5, mule_scale=0,
        lo=0, hi=50, dist="poisson",
    )

    # 14. international_tx_ratio
    data["international_tx_ratio"] = _ratio(0.04, 0.04, 0.30, 0.14)

    # 15. dormancy_before_activity_days
    data["dormancy_before_activity_days"] = _base(
        normal_loc=5, normal_scale=8,
        mule_loc=90, mule_scale=50,
        lo=0, hi=1000,
    )

    # 16. avg_time_between_tx_hours
    data["avg_time_between_tx_hours"] = _base(
        normal_loc=48, normal_scale=30,
        mule_loc=4, mule_scale=3,
        lo=0.1, hi=720,
    )

    # 17. max_single_tx_amount (log-normal)
    data["max_single_tx_amount"] = _base(
        normal_loc=7.5, normal_scale=1.5,
        mule_loc=9.5, mule_scale=1.0,
        lo=1, hi=1_000_000, dist="lognormal",
    )

    # 18. round_amount_ratio — structuring / smurfing
    data["round_amount_ratio"] = _ratio(0.12, 0.08, 0.55, 0.15)

    # 19. same_day_inout_count
    data["same_day_inout_count"] = _base(
        normal_loc=0.3, normal_scale=0,
        mule_loc=6, mule_scale=0,
        lo=0, hi=50, dist="poisson",
    )

    # 20. weekend_tx_ratio
    data["weekend_tx_ratio"] = _ratio(0.15, 0.08, 0.40, 0.12)

    # 21. atm_withdrawal_ratio
    data["atm_withdrawal_ratio"] = _ratio(0.08, 0.06, 0.35, 0.12)

    # 22. ip_change_count_30d
    data["ip_change_count_30d"] = _base(
        normal_loc=1.5, normal_scale=0,
        mule_loc=8, mule_scale=0,
        lo=0, hi=60, dist="poisson",
    )

    # 23. peer_to_peer_tx_ratio
    data["peer_to_peer_tx_ratio"] = _ratio(0.20, 0.12, 0.65, 0.15)

    # 24. declined_tx_ratio
    data["declined_tx_ratio"] = _ratio(0.02, 0.02, 0.12, 0.06)

    # 25. multi_currency_flag (bool)
    mc = np.zeros(n, dtype=np.int8)
    mc[~is_mule] = rng.choice([0, 1], size=n_normal, p=[0.92, 0.08])
    mc[mule_indices[~near_miss_mask[mule_indices]]] = rng.choice(
        [0, 1],
        size=len(mule_indices[~near_miss_mask[mule_indices]]),
        p=[0.40, 0.60],
    )
    mc[mule_indices[near_miss_mask[mule_indices]]] = rng.choice(
        [0, 1],
        size=len(mule_indices[near_miss_mask[mule_indices]]),
        p=[0.92, 0.08],
    )
    data["multi_currency_flag"] = mc

    # 26. avg_balance_30d (log-normal; mules keep low balances)
    data["avg_balance_30d"] = _base(
        normal_loc=8.5, normal_scale=1.5,
        mule_loc=5.5, mule_scale=1.0,
        lo=0, hi=5_000_000, dist="lognormal",
    )

    # 27. balance_velocity (std of daily balance / mean balance)
    data["balance_velocity"] = _base(
        normal_loc=0.15, normal_scale=0.10,
        mule_loc=0.70, mule_scale=0.20,
        lo=0, hi=5.0,
    )

    # 28. linked_accounts_count
    data["linked_accounts_count"] = _base(
        normal_loc=1.2, normal_scale=0,
        mule_loc=5, mule_scale=0,
        lo=0, hi=30, dist="poisson",
    )

    # 29. phone_change_flag (bool)
    pc = np.zeros(n, dtype=np.int8)
    pc[~is_mule] = rng.choice([0, 1], size=n_normal, p=[0.96, 0.04])
    pc[mule_indices[~near_miss_mask[mule_indices]]] = rng.choice(
        [0, 1],
        size=len(mule_indices[~near_miss_mask[mule_indices]]),
        p=[0.55, 0.45],
    )
    pc[mule_indices[near_miss_mask[mule_indices]]] = rng.choice(
        [0, 1],
        size=len(mule_indices[near_miss_mask[mule_indices]]),
        p=[0.96, 0.04],
    )
    data["phone_change_flag"] = pc

    # 30. email_domain_freemail (bool)
    ef = np.zeros(n, dtype=np.int8)
    ef[~is_mule] = rng.choice([0, 1], size=n_normal, p=[0.55, 0.45])
    ef[mule_indices[~near_miss_mask[mule_indices]]] = rng.choice(
        [0, 1],
        size=len(mule_indices[~near_miss_mask[mule_indices]]),
        p=[0.20, 0.80],
    )
    ef[mule_indices[near_miss_mask[mule_indices]]] = rng.choice(
        [0, 1],
        size=len(mule_indices[near_miss_mask[mule_indices]]),
        p=[0.55, 0.45],
    )
    data["email_domain_freemail"] = ef

    # ==================================================================
    #  False-positive noise: push 1–2 random features for selected
    #  normal accounts into mule-like ranges
    # ==================================================================
    noisy_features = [
        "rapid_inout_ratio", "cash_deposit_ratio", "night_tx_ratio",
        "round_amount_ratio", "same_day_inout_count", "tx_count_30d",
        "unique_remitters_30d", "peer_to_peer_tx_ratio",
        "balance_velocity", "ip_change_count_30d",
    ]
    for idx in fp_idx:
        n_push = rng.integers(1, 3)  # 1 or 2 features
        chosen = rng.choice(noisy_features, size=n_push, replace=False)
        for feat in chosen:
            current_val = data[feat][idx]
            # Push the value up by 2–4× its current value or to a mule-like
            # minimum, whichever is larger.
            bump = rng.uniform(2.0, 4.0)
            data[feat][idx] = min(current_val * bump + rng.uniform(0.05, 0.3), 1.0) \
                if "ratio" in feat \
                else current_val * bump + rng.uniform(1, 5)

    # ==================================================================
    #  Assemble DataFrame
    # ==================================================================
    df = pd.DataFrame(data)

    # Round integer-like columns for cleanliness
    int_cols = [
        "account_age_days", "tx_count_30d", "unique_remitters_30d",
        "unique_beneficiaries_30d", "device_change_count_30d",
        "login_frequency_30d", "failed_login_count_30d",
        "dormancy_before_activity_days", "same_day_inout_count",
        "ip_change_count_30d", "linked_accounts_count",
    ]
    for c in int_cols:
        df[c] = df[c].round(0).astype(int)

    # Round monetary / continuous columns to 2 decimals
    float_cols = [c for c in df.columns if c not in int_cols and df[c].dtype != np.int8]
    for c in float_cols:
        df[c] = df[c].round(4)

    # Boolean columns as int {0, 1}
    for c in ["kyc_complete", "multi_currency_flag", "phone_change_flag",
              "email_domain_freemail"]:
        df[c] = df[c].astype(int)

    # Label column
    df["is_mule"] = labels

    # Shuffle rows so mules aren't clustered at the end
    df = df.sample(frac=1, random_state=seed).reset_index(drop=True)

    return df


# ---------------------------------------------------------------------------
#  Pretty-print summary statistics
# ---------------------------------------------------------------------------
def print_summary(df: pd.DataFrame) -> None:
    """Print class balance and feature statistics."""
    sep = "═" * 72
    print(f"\n{sep}")
    print("  MULESHIELD — Synthetic Dataset Summary")
    print(sep)

    total = len(df)
    mules = df["is_mule"].sum()
    normals = total - mules
    print(f"\n  Total accounts : {total:,}")
    print(f"  Normal (0)     : {normals:,}  ({normals / total:.2%})")
    print(f"  Mule   (1)     : {mules:,}  ({mules / total:.2%})")

    print(f"\n{'─' * 72}")
    print("  Feature Statistics (all accounts)")
    print(f"{'─' * 72}")

    stats = df.drop(columns=["is_mule"]).describe().T
    stats = stats[["mean", "std", "min", "25%", "50%", "75%", "max"]]
    with pd.option_context(
        "display.max_rows", 40,
        "display.float_format", "{:.2f}".format,
        "display.width", 120,
    ):
        print(stats.to_string())

    print(f"\n{'─' * 72}")
    print("  Mean comparison: Normal vs Mule")
    print(f"{'─' * 72}")

    comparison = df.groupby("is_mule").mean(numeric_only=True).T
    comparison.columns = ["Normal (0)", "Mule (1)"]
    with pd.option_context(
        "display.max_rows", 40,
        "display.float_format", "{:.2f}".format,
        "display.width", 120,
    ):
        print(comparison.to_string())

    print(f"\n{sep}\n")


# ---------------------------------------------------------------------------
#  CLI entry-point
# ---------------------------------------------------------------------------
def main() -> None:
    here = pathlib.Path(__file__).resolve().parent
    out_path = here / "synthetic_accounts.csv"

    df = generate_dataset(n=8_000, mule_rate=0.009, seed=42)

    df.to_csv(out_path, index=False)
    print(f"✓ Saved {len(df):,} rows → {out_path}")

    print_summary(df)


if __name__ == "__main__":
    main()
