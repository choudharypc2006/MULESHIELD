# MULESHIELD — Feature Data Dictionary

> **Dataset**: `synthetic_accounts.csv`
> **Records**: ~8 000 synthetic bank-account profiles
> **Label**: `is_mule` (binary, ~0.9 % positive rate)

---

## Feature Reference

| # | Feature | Type | Range | Description | Fraud Relevance |
|---|---------|------|-------|-------------|-----------------|
| 1 | `account_age_days` | int | 7 – 7 300 | Days since the account was opened. | Mule accounts are often freshly opened or recently purchased dormant accounts. Short account age is a strong risk signal. |
| 2 | `tx_count_30d` | int | 0 – 500 | Total transaction count in the last 30 days. | Mule accounts exhibit abnormally high throughput as funds are cycled rapidly. |
| 3 | `unique_remitters_30d` | int | 0 – 200 | Number of distinct senders in 30 days. | A high number of unique remitters suggests the account is receiving money from many victims or co-conspirators. |
| 4 | `unique_beneficiaries_30d` | int | 0 – 200 | Number of distinct recipients in 30 days. | Rapid fan-out to many beneficiaries is a hallmark of layering — distributing illicit funds to obscure their origin. |
| 5 | `rapid_inout_ratio` | float | 0.0 – 1.0 | Fraction of incoming funds that leave within 60 minutes. | Pass-through behaviour — money entering and exiting quickly — is the defining pattern of a mule account. |
| 6 | `cash_deposit_ratio` | float | 0.0 – 1.0 | Fraction of deposits made in cash. | Cash deposits are harder to trace and are frequently used to inject illicit funds into the banking system. |
| 7 | `night_tx_ratio` | float | 0.0 – 1.0 | Fraction of transactions occurring between 00:00 – 06:00. | Automated or scripted transfers often run overnight to avoid real-time monitoring by compliance teams. |
| 8 | `device_change_count_30d` | int | 0 – 30 | Number of distinct devices used to access the account in 30 days. | Multiple device changes suggest account sharing, compromise, or access by a fraud ring. |
| 9 | `avg_tx_amount` | float | 1 – 500 000 | Mean transaction amount (currency units). | Mule accounts often have elevated average amounts as they move large sums quickly. |
| 10 | `tx_amount_std` | float | 0 – 500 000 | Standard deviation of transaction amounts. | High variability can indicate structured (smurfed) transactions mixed with large lump-sum transfers. |
| 11 | `kyc_complete` | bool (0/1) | {0, 1} | Whether full Know-Your-Customer verification is complete. | Incomplete KYC allows fraudsters to operate with minimal identity verification, raising risk. |
| 12 | `login_frequency_30d` | int | 0 – 300 | Number of login sessions in 30 days. | Elevated login frequency may indicate bot activity, credential sharing, or manual monitoring of fund movements. |
| 13 | `failed_login_count_30d` | int | 0 – 50 | Number of failed login attempts in 30 days. | May indicate credential stuffing, brute-force attempts, or an account being tested by a new holder. |
| 14 | `international_tx_ratio` | float | 0.0 – 1.0 | Fraction of transactions involving a foreign counterpart. | Cross-border transfers are a primary mechanism for laundering money across jurisdictions. |
| 15 | `dormancy_before_activity_days` | int | 0 – 1 000 | Days the account was dormant before the current activity burst. | Fraudsters often buy or recruit dormant accounts, reactivating them suddenly for mule operations. |
| 16 | `avg_time_between_tx_hours` | float | 0.1 – 720 | Mean hours between consecutive transactions. | Very short inter-transaction times suggest automated cycling; organic accounts show wider, irregular spacing. |
| 17 | `max_single_tx_amount` | float | 1 – 1 000 000 | Largest single transaction in 30 days. | Outlier large transfers may be the "big move" in a layering scheme before the account is abandoned. |
| 18 | `round_amount_ratio` | float | 0.0 – 1.0 | Fraction of transactions at round-number amounts (e.g., 500, 1 000). | Structuring (smurfing) often uses round amounts to stay below reporting thresholds. |
| 19 | `same_day_inout_count` | int | 0 – 50 | Number of days in the last 30 with both incoming and outgoing transactions on the same day. | Consistent same-day in/out is a strong indicator of pass-through mule activity. |
| 20 | `weekend_tx_ratio` | float | 0.0 – 1.0 | Fraction of transactions occurring on Saturday / Sunday. | Legitimate business accounts are less active on weekends; mule activity often continues without pause. |
| 21 | `atm_withdrawal_ratio` | float | 0.0 – 1.0 | Fraction of outflows via ATM cash withdrawals. | ATM cash-out is a common endpoint for mule-account schemes, converting electronic funds to untraceable cash. |
| 22 | `ip_change_count_30d` | int | 0 – 60 | Number of distinct IP addresses used to access the account in 30 days. | High IP diversity suggests VPN usage, geographic mobility, or account access by multiple actors. |
| 23 | `peer_to_peer_tx_ratio` | float | 0.0 – 1.0 | Fraction of transactions that are person-to-person transfers. | P2P transfers are preferred for layering because they mimic legitimate social payments. |
| 24 | `declined_tx_ratio` | float | 0.0 – 1.0 | Fraction of attempted transactions that were declined. | Elevated declines may indicate probing of account limits or testing stolen credentials. |
| 25 | `multi_currency_flag` | bool (0/1) | {0, 1} | Whether the account transacts in more than one currency. | Multi-currency activity complicates tracing and is common in cross-border laundering schemes. |
| 26 | `avg_balance_30d` | float | 0 – 5 000 000 | Average daily balance over 30 days. | Mule accounts typically maintain very low balances relative to their throughput — money doesn't linger. |
| 27 | `balance_velocity` | float | 0.0 – 5.0 | Coefficient of variation of daily balance (σ / μ). | High balance velocity means the balance swings wildly, consistent with rapid in-then-out fund movement. |
| 28 | `linked_accounts_count` | int | 0 – 30 | Number of other accounts linked (same name, address, phone, or device). | Nominee networks of multiple accounts under coordinated control are a hallmark of organised mule operations. |
| 29 | `phone_change_flag` | bool (0/1) | {0, 1} | Whether the account's registered phone number was changed in the last 30 days. | Phone changes (especially SIM swaps) can indicate account takeover or preparation for mule use. |
| 30 | `email_domain_freemail` | bool (0/1) | {0, 1} | Whether the registered email uses a free-mail provider (Gmail, Yahoo, etc.). | While common, free-mail domains are over-represented in fraudulent accounts due to easy, anonymous creation. |

---

## Label

| Column | Type | Values | Description |
|--------|------|--------|-------------|
| `is_mule` | int | {0, 1} | **Target variable.** 1 = suspected mule account, 0 = normal account. Approximately 0.9 % of accounts are mules. |

---

## Noise & Overlap Design

To ensure the dataset is **not perfectly separable** (mirroring real-world conditions):

- **Near-miss mules (~15 % of mule accounts):** Generated using *normal-account* distributions so their feature profiles are nearly indistinguishable from legitimate accounts.
- **False-positive normals (~5 % of normal accounts):** 1–2 randomly selected features are pushed into mule-like ranges, simulating legitimate accounts that would trigger naive rules.

This deliberate overlap ensures that any model trained on this data must learn nuanced patterns rather than relying on simple thresholds.

---

## Feature Clusters

The 30 features can be grouped thematically for analysis:

| Cluster | Features |
|---------|----------|
| **Account Profile** | `account_age_days`, `kyc_complete`, `avg_balance_30d`, `linked_accounts_count` |
| **Transaction Volume** | `tx_count_30d`, `unique_remitters_30d`, `unique_beneficiaries_30d`, `same_day_inout_count` |
| **Transaction Amounts** | `avg_tx_amount`, `tx_amount_std`, `max_single_tx_amount`, `round_amount_ratio` |
| **Temporal Patterns** | `night_tx_ratio`, `weekend_tx_ratio`, `avg_time_between_tx_hours`, `dormancy_before_activity_days` |
| **Flow Behaviour** | `rapid_inout_ratio`, `cash_deposit_ratio`, `atm_withdrawal_ratio`, `peer_to_peer_tx_ratio`, `international_tx_ratio`, `balance_velocity` |
| **Access & Device** | `device_change_count_30d`, `ip_change_count_30d`, `login_frequency_30d`, `failed_login_count_30d` |
| **Identity Signals** | `phone_change_flag`, `email_domain_freemail`, `multi_currency_flag`, `declined_tx_ratio` |
