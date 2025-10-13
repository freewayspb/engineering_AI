# Prototype Metrics - Agreement Sheet
Version: 0.1 (draft)
Date: 01.10.2025

---

## 1. Prototype-level KPIs

| Prototype | Goal | Metrics | Target (TBD) | Notes |
|---|---|---|---|---|
| OCR | Reliable recognition on client samples | CER/WER; Processing time per doc | CER/WER ≤ [TBD_Discuss]; ≤ 30s | Noise/quality sensitivity captured in test set |
| Structuring | Valid structured outputs | Valid records %; Schema errors | ≥ 99% valid | JSON Schema as reference |
| Classification | Thematic assignment | macro‑F1; Coverage | macro‑F1 ≥ [TBD_Discuss] | Category set agreed with client |
| DWG parsing | Minimal attributes extracted | Entities/attributes coverage | [TBD_Discuss] | Define minimal DWG entities list |
| Estimates (ARP/GSFX) | Minimal fields extracted | Key fields completeness | [TBD_Discuss] | Define minimal fields list |

---

## 2. Operational metrics (for prototype stage)

- Batch processing supported (Yes/No)
- Reproducibility (fixed versions, deterministic runs)
- Artifact outputs: JSON/CSV/XLSX, validation reports

---

## 3. Open items

| ID | Topic | Question | Owner | Due | Status |
|---|---|---|---|---|---|
| M‑01 | OCR thresholds | Agree CER/WER thresholds | BA/Client | TBD | Open |
| M‑02 | Classification | Agree macro‑F1 threshold | BA/Client | TBD | Open |
| M‑03 | Structuring | Define validity threshold | BA/Client | TBD | Open |
| M‑04 | DWG scope | Minimal entities list | BA/Arch/Client | TBD | Open |
| M‑05 | Estimates scope | Minimal fields list | BA/Client | TBD | Open |
