# Claims Audit & Calibrated Language Specification

**Document:** `docs/CLAIMS_AUDIT.md`  
**Purpose:** Comprehensive audit of user-facing claims, citations, and model explanations across the Wind Day-Ahead Estimator application, aligning with Milestone M5 of `AGENT_PLAN.md`.

---

## 1. Primary Source Citations for Datasets

### 1.1 WINDFOR (Day-Ahead Wind Generation Forecast)
* **Dataset Identifier:** `WINDFOR`
* **Publisher:** National Energy System Operator (NESO) via Elexon Insights Solution (formerly BMRS).
* **Endpoint:** `https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR`
* **Access Date:** October 2026
* **Exact Description:**  
  > *"WINDFOR provides forward-looking generation forecasts for all visible Power Park Modules (wind farms connected to the transmission system or holding operational metering visible to the ESO) in Great Britain, published up to 8 times daily."*

### 1.2 FUELHH (Half-Hourly Generation Outturn by Fuel Type)
* **Dataset Identifier:** `FUELHH`
* **Publisher:** Elexon Insights Solution (derived from operational metering).
* **Endpoint:** `https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH`
* **Access Date:** October 2026
* **Exact Description:**  
  > *"FUELHH provides half-hourly generation outturn by fuel type, derived from Operational Metering for Balancing Mechanism Units (BMUs) connected directly to the National Transmission System. Embedded generation and smaller assets lacking transmission-level operational meters are excluded or unmetered."*

### 1.3 Definitional Gap Reconciliation
* **Unverified Claims Removed:**
  - Removed unverified "82% to 85%" visibility ratio citation.
  - Removed uncited "BSC Section Q Operational Metering" and "NESO System Visibility Guidance" specific references.
* **Calibrated Statement:**  
  > *"WINDFOR forecasts aggregate expected generation across visible wind farms, whereas FUELHH outturn records generation strictly from transmission-connected Balancing Mechanism Units (BMUs). This scoping difference means WINDFOR naturally measures a wider perimeter than FUELHH. Across January 2026, raw WINDFOR exceeded FUELHH outturn by 15.5% of outturn (13.4% of forecast). While the transmission BMU boundary explains a substantial portion of this discrepancy, the exact quantitative split between metering perimeter differences and weather forecast error is not separated in Elexon's public schemas and remains an unexplained gap."*

---

## 2. Accurate Model Timeline & Disclosure

| Aspect | Previous Overclaiming Text | Calibrated & Audited Text |
|---|---|---|
| **Model Timeline** | *"Parameters fixed in advance, not re-tuned after seeing outturn"* | *"v1 (additive) and flat 15% were established a priori; v2 (proportional) and expanding ratio were designed post-hoc after observing regime shifts. Candidate models were selected on January 1–15 decisions via a pre-registered protocol (docs/PROTOCOL.md) and evaluated once on the January 16–30 holdout."* |
| **Sample Size** | *"Statistically proven across Great Britain"* | *"Evidence is based on a 1-month historical replay (January 2026, 30 decision days, 1,440 settlement intervals). A single month is a limited sample and performance under other weather regimes may differ."* |
| **Certainty & Proof** | *"Guarantees persistent shortfall reduction"* / *"Verified Parquet replay cache"* | *"Can systematically reduce shortfall frequency"* / *"Replay cache (SHA-256: d997afe4...)"* |
| **Audit Language** | *"Official National Grid audit trail"* | *"Reproducible historical replay log from Elexon BMRS public settlement data"* |
| **Metric Clarity** | *"30 of 30 days reduced shortfall"* | *"Days where break-even < 2x (avoided shortfall exceeded extra supply: 22 of 30 days for flat 15%, 17 of 30 days for v1)"* |
| **Publication Lag** | Stated as factual publication timing | Explicitly marked: *"1-hour publication lag is an operational assumption"* |
| **Bias Denominator** | Inconsistently stated as "+15.5%" or "+13.2 GW%" | Standardized and explicitly labelled: *"+15.5% of outturn (+13.4% of forecast)"* |

---

## 3. Checklist of Changed Strings by File

### 3.1 `frontend/src/components/EstimateDeepDive.tsx`
- **Line ~404:** Updated Definitional Scoping Difference to quote primary source definitions for `WINDFOR` and `FUELHH`, removed "82% to 85%", and noted that the exact decomposition remains unexplained.
- **Line ~360:** Updated bias description to explicitly state "13.4% of forecast (15.5% of outturn)".
- **Line ~1150:** Provenance card verified: references "Replay cache", displays SHA-256 hash.

### 3.2 `frontend/src/pages/CheckPage.tsx`
- **Line ~166:** Updated Definitional Boundary Citation with Elexon Insights URLs and exact quotes; removed unverified 82–85% capacity statement; labelled 1-hour lag as assumption.

### 3.3 `frontend/src/pages/DocsPage.tsx`
- **Section 2:** Updated Definitional paragraph with primary quotes and URLs; removed BSC Section Q and NESO 82–85% unverified claims.
- **Section 3:** Replaced "parameters fixed in advance" with explicit protocol timeline (M3: Selection half Jan 1–15, holdout Jan 16–30, 1-month sample limitation).
- **Section 4:** Explicitly labelled 1-hour publication lag as an operational assumption.

### 3.4 `frontend/src/components/CostRatioCalculator.tsx`
- Added explicit note: *"Note: This calculation treats extra advance power as unrecoverable, which overstates the cost when surplus can be resold."*
- Default view set to normalized per 100 MWh delivered volume.
- Removed default GB-wide £ headline in favor of user portfolio context.
