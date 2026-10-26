# Claims Audit & Calibrated Language Specification

**Document:** `docs/CLAIMS_AUDIT.md`  
**Purpose:** Comprehensive audit of user-facing claims, citations, and model explanations across the Wind Day-Ahead Estimator application, fulfilling Milestone R3 (Findings F3 and F10).

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

## 2. Claims Audit Table (File-by-File Mapping)

Every user-facing statement regarding model timing, certainty, data boundaries, and performance has been audited and mapped to its resolution status (**Fixed**, **Softened**, or **Reframed**):

| Domain / Claim Topic | File(s) | Previous Overclaiming Text | Calibrated & Audited Text | Status |
|---|---|---|---|---|
| **Model Protocol Framing** | `docs/PROTOCOL.md`, `README.md` | *"Claimed pre-commitment of protocol"* | *"Post-hoc model comparison with a pre-stated selection rule"* (full git chronology disclosed: holdout was evaluated in commit `0b8ee92` before protocol was written in `979d1ce`) | **Reframed** |
| **Historical Replay Framing (Jan 2026)** | `frontend/src/pages/DocsPage.tsx`, `README.md` | *"Holdout rolling window"* | *"Empirical rolling calibration window respecting 09:00 UTC daily cutoffs"* (true holdout reserved for post-January in `docs/VALIDATION.md`) | **Fixed** |
| **Model Parameter Timing** | `frontend/src/pages/DocsPage.tsx`, `docs/PROTOCOL.md` | *"Parameters fixed beforehand with zero backward look"* | *"Parameters configured prior to evaluation; v1 and flat 15% were initial baselines, while v2 and expanding ratio were formulated post-hoc"* | **Fixed** |
| **Dataset Authority** | `frontend/src/pages/LandingPage.tsx`, `frontend/src/pages/DocsPage.tsx`, `README.md` | *"Authoritative Elexon BMRS API"* / *"Authoritative WINDFOR"* | *"Public Elexon BMRS API"* / *"Published WINDFOR forecast"* | **Fixed** |
| **Audit Trail Certainty** | `LandingPage.tsx`, `README.md` | *"Validated by 5 automated replay isolation tests"* / *"Validated Parquet replay cache"* | *"Evaluated across 7 automated replay isolation tests"* / *"Replay cache (SHA-256: d997afe4...)"* | **Fixed** |
| **Leakage & Performance Guarantees** | `frontend/src/pages/LandingPage.tsx`, `README.md`, `Footer.tsx` | *"No Future Leakage Guarantee"* / *"Honesty Guarantee"* / *"cash savings guarantees"* | *"Strict Zero-Future-Data-Leakage Policy"* / *"Honest Reporting (no guarantee of net savings)"* / *"does not guarantee cash savings"* | **Softened** |
| **FAQ Performance Assurance** | `EstimateFaq.tsx`, `EstimateDeepDive.tsx` | *"Is this guaranteed?"* (followed by unmitigated claims) | *"Is performance guaranteed? (No guarantee)"* (explicitly stating: no guarantee; margin can fail under regime shifts) | **Softened** |
| **Economic Break-Even Formula** | `CostRatioCalculator.tsx`, `README.md`, `DocsPage.tsx` | *"Break-even ratio = Extra / Avoided (0.89x)"* | *"Corrected break-even: k* = 1 + (1-s)*Extra/Avoided (1.405x for flat 15%, 1.886x for v2 at s=0)"* | **Fixed** |
| **Equal-Cost Framing** | `ShortfallComparisonBars.tsx`, `ComparativeAnalysisSection.tsx`, `schemas.py` | *"30 of 30 days reduced shortfall (equal-cost break-even)"* | *"Days where break-even < 2x (avoided shortfall exceeded extra supply: 22 of 30 days for flat 15%)"* | **Fixed** |
| **Surplus Recovery Accounting** | `CostRatioCalculator.tsx`, `economics.py` | Hidden $s=0$ assumption without user controls | Explicit surplus recovery slider $s \in [0.0, 1.0]$ defaulting to conservative $s=0.0$, plus loss disclosures at $k=1.0$ | **Fixed** |
| **Publication Lag Disclosure** | `CheckPage.tsx`, `EstimateDeepDive.tsx`, `DocsPage.tsx` | Stated as factual publication timing | Explicitly marked: *"1-hour publication lag is an operational assumption"* | **Softened** |
| **Level Bias Metric Precision** | `LandingPage.tsx`, `DocsPage.tsx`, `EstimateDeepDive.tsx` | Inconsistently stated as "+15.5%" or "+13.2 GW%" | Standardized and explicitly labelled: *"+15.5% of outturn (+13.4% of forecast)"* | **Fixed** |

---

## 3. Automated Verification

Compliance with this calibrated language standard is continuously enforced via `pytest backend/tests/test_claims_lint.py`. The test scans all frontend components, backend routers, documentation files, and the README for banned phrases, ensuring no regression into unverified marketing language.
