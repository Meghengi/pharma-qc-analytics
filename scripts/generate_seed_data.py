"""
Generates synthetic seed data for the pharma-qc-analytics demo project.

Everything here is fictional: product names, lot numbers, specifications,
and test results are all randomly generated and do not represent any real
company, product, or test data. Written with no third-party dependencies
(stdlib only). Output lands in ../seeds/ as dbt seed CSVs.

Run:
    python3 generate_seed_data.py
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(7)  # deterministic output so the repo's data is reproducible

SEED_DIR = Path(__file__).resolve().parent.parent / "seeds"
SEED_DIR.mkdir(exist_ok=True)

# Fictional small-molecule drug products, each with its own release testing panel.
PRODUCTS = [
    {"product_code": "ALZ-100", "product_name": "Alzorin 100mg Tablet", "dosage_form": "Tablet"},
    {"product_code": "BRN-250", "product_name": "Brenavix 250mg Capsule", "dosage_form": "Capsule"},
    {"product_code": "CTX-50",  "product_name": "Cortexin 50mg Tablet",  "dosage_form": "Tablet"},
    {"product_code": "DLV-10",  "product_name": "Delvara 10mg/mL Injection", "dosage_form": "Injection"},
    {"product_code": "ERN-500", "product_name": "Ernovix 500mg Tablet",  "dosage_form": "Tablet"},
]

# Each test has a target and a spec range; result generation below biases
# most lots to pass comfortably, a smaller share to pass near the limit,
# and a small share to fail (OOS) — roughly mirroring a real release-testing
# pass-rate profile.
TEST_PANEL = {
    "Assay (% of label claim)": {"target": 100.0, "lsl": 95.0, "usl": 105.0, "unit": "%"},
    "Dissolution Q30 (%)": {"target": 92.0, "lsl": 80.0, "usl": None, "unit": "%"},
    "Related Substances - Total Impurities (%)": {"target": 0.15, "lsl": None, "usl": 0.5, "unit": "%"},
    "Water Content (%)": {"target": 2.0, "lsl": None, "usl": 4.0, "unit": "%"},
    "Content Uniformity (AV)": {"target": 4.0, "lsl": None, "usl": 15.0, "unit": "AV"},
}

ANALYSTS = ["J. Alvarez", "M. Chen", "R. Okafor", "S. Patel", "T. Novak", "K. Fischer", "D. Ibrahim"]
SHIFTS = ["Day", "Swing", "Night"]
INSTRUMENTS = ["HPLC-04", "HPLC-07", "HPLC-11", "UV-02", "KF-Titrator-01", "Dissolution-Bath-3"]

DEVIATION_CATEGORIES = [
    "Out-of-Specification result",
    "Out-of-Trend result",
    "Equipment malfunction",
    "Sampling error",
    "Documentation error",
    "Environmental excursion",
]
DEVIATION_IMPACT = ["No product impact", "Batch quarantined", "Batch rejected", "CAPA initiated"]


def random_date(start: date, end: date) -> date:
    return start + timedelta(days=random.randint(0, (end - start).days))


def gen_batches(n_per_product=40):
    start = date(2024, 1, 1)
    end = date(2025, 11, 1)
    rows = []
    batch_num = 1
    for product in PRODUCTS:
        for _ in range(n_per_product):
            mfg_date = random_date(start, end)
            batch_id = f"{product['product_code']}-{mfg_date.strftime('%y%m')}-{batch_num:04d}"
            rows.append({
                "batch_id": batch_id,
                "product_code": product["product_code"],
                "batch_size_units": random.choice([50000, 100000, 150000, 250000]),
                "manufacture_date": mfg_date.isoformat(),
                "line": random.choice(["Line-A", "Line-B", "Line-C"]),
            })
            batch_num += 1
    return rows


def sample_result(spec):
    """Mostly pass comfortably, sometimes pass near a limit, rarely fail (OOS)."""
    target = spec["target"]
    lsl, usl = spec["lsl"], spec["usl"]
    roll = random.random()
    if roll < 0.90:
        # normal variation around target, scaled to spec width
        width = (usl - target) if usl is not None else (target - lsl if lsl is not None else target * 0.03)
        spread = abs(width) * 0.35
        value = random.gauss(target, max(spread, 0.01))
    elif roll < 0.97:
        # near a limit but still passing
        limit = usl if usl is not None else lsl
        value = limit - (limit - target) * random.uniform(0.02, 0.15) if usl is not None else limit + (target - limit) * random.uniform(0.02, 0.15)
    else:
        # out of specification - breach whichever limit exists
        if usl is not None and (lsl is None or random.random() < 0.6):
            value = usl * random.uniform(1.01, 1.08)
        else:
            value = lsl * random.uniform(0.85, 0.98)
    return round(value, 3)


def result_status(value, spec):
    lsl, usl = spec["lsl"], spec["usl"]
    if lsl is not None and value < lsl:
        return "OOS"
    if usl is not None and value > usl:
        return "OOS"
    return "Pass"


def gen_specifications():
    rows = []
    spec_id = 1
    for test_name, spec in TEST_PANEL.items():
        for product in PRODUCTS:
            rows.append({
                "spec_id": spec_id,
                "product_code": product["product_code"],
                "test_name": test_name,
                "lower_spec_limit": spec["lsl"] if spec["lsl"] is not None else "",
                "upper_spec_limit": spec["usl"] if spec["usl"] is not None else "",
                "unit": spec["unit"],
            })
            spec_id += 1
    return rows


def gen_qc_results(batches):
    rows = []
    result_id = 1
    for batch in batches:
        mfg_date = date.fromisoformat(batch["manufacture_date"])
        test_date = mfg_date + timedelta(days=random.randint(1, 5))
        for test_name, spec in TEST_PANEL.items():
            value = sample_result(spec)
            status = result_status(value, spec)
            rows.append({
                "result_id": result_id,
                "batch_id": batch["batch_id"],
                "test_name": test_name,
                "result_value": value,
                "unit": spec["unit"],
                "test_date": test_date.isoformat(),
                "analyst": random.choice(ANALYSTS),
                "shift": random.choice(SHIFTS),
                "instrument_id": random.choice(INSTRUMENTS),
                "status": status,
            })
            result_id += 1
    return rows


def gen_deviations(qc_results, batches):
    """One deviation record for most (not all) OOS results, plus a handful of
    non-OOS process deviations, to make the deviations table realistically
    broader than "just a mirror of OOS results"."""
    rows = []
    dev_id = 1
    batch_by_id = {b["batch_id"]: b for b in batches}

    oos_results = [r for r in qc_results if r["status"] == "OOS"]
    for r in oos_results:
        if random.random() < 0.92:  # a few OOS results get bundled into one deviation; keep simple here
            opened = date.fromisoformat(r["test_date"]) + timedelta(days=random.randint(0, 2))
            closed_lag = random.choices([3, 5, 8, 14, 21, 30], weights=[10, 20, 25, 25, 15, 5])[0]
            rows.append({
                "deviation_id": f"DEV-{dev_id:05d}",
                "batch_id": r["batch_id"],
                "related_result_id": r["result_id"],
                "category": "Out-of-Specification result",
                "opened_date": opened.isoformat(),
                "closed_date": (opened + timedelta(days=closed_lag)).isoformat(),
                "impact": random.choices(
                    ["Batch quarantined", "Batch rejected", "CAPA initiated"],
                    weights=[45, 30, 25],
                )[0],
            })
            dev_id += 1

    # sprinkle in some unrelated process deviations not tied to a specific result
    for _ in range(45):
        batch = random.choice(batches)
        mfg_date = date.fromisoformat(batch["manufacture_date"])
        opened = mfg_date + timedelta(days=random.randint(0, 10))
        closed_lag = random.choices([2, 4, 7, 12, 20], weights=[20, 25, 25, 20, 10])[0]
        rows.append({
            "deviation_id": f"DEV-{dev_id:05d}",
            "batch_id": batch["batch_id"],
            "related_result_id": "",
            "category": random.choice(DEVIATION_CATEGORIES[1:]),
            "opened_date": opened.isoformat(),
            "closed_date": (opened + timedelta(days=closed_lag)).isoformat(),
            "impact": random.choices(DEVIATION_IMPACT, weights=[55, 25, 10, 10])[0],
        })
        dev_id += 1

    return rows


def write_csv(rows, filename):
    path = SEED_DIR / filename
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows):>5} rows -> {path.relative_to(SEED_DIR.parent)}")


def main():
    batches = gen_batches()
    specifications = gen_specifications()
    qc_results = gen_qc_results(batches)
    deviations = gen_deviations(qc_results, batches)

    products_rows = PRODUCTS

    write_csv(products_rows, "raw_products.csv")
    write_csv(batches, "raw_batches.csv")
    write_csv(specifications, "raw_specifications.csv")
    write_csv(qc_results, "raw_qc_results.csv")
    write_csv(deviations, "raw_deviations.csv")


if __name__ == "__main__":
    main()
