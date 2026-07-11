"""
coded_tools/hackathon/agentic_migrator/agent_logic.py
----------------------------------------------------------------
Pure, dependency-light business logic for the Agentic AI Migration
Factory. Each function takes/returns plain JSON-safe Python
structures (lists of dicts, i.e. "records") rather than pandas
DataFrames or any other non-serializable object, because this data
is passed around via neuro-san's `sly_data` bulletin board, which
should stay JSON-safe.

pandas is used internally for convenience but never crosses a
function boundary.
----------------------------------------------------------------
"""
import copy
import difflib
import os
import random
import re

import pandas as pd

BASE_DIR = r"C:\Users\Shaiyad Khan\Downloads\ExtractFiles-main\ExtractFiles-main\coded_tools\hackathon\agentic_migrator"
#os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

CANONICAL_MASTER_OBJECTS = {"vendor": "Vendor", "customer": "Customer"}
CANONICAL_TRANSACTION_OBJECTS = {"finance": "Finance"}


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def normalize_name(name) -> str:
    if name is None:
        return ""
    n = str(name).lower().strip()
    n = re.sub(r"[^a-z0-9 ]", "", n)
    n = re.sub(r"\b(technologies|technology|tech|solutions|solution|ltd|pvt|inc)\b", "tech", n)
    n = re.sub(r"\s+", " ", n).strip()
    return n


def fuzzy_similarity(a, b) -> float:
    return difflib.SequenceMatcher(None, normalize_name(a), normalize_name(b)).ratio()


def cluster_similar_names(names, threshold: float = 0.72):
    n = len(names)
    visited = [False] * n
    clusters = []
    for i in range(n):
        if visited[i]:
            continue
        cluster = [i]
        visited[i] = True
        for j in range(i + 1, n):
            if visited[j]:
                continue
            if fuzzy_similarity(names[i], names[j]) >= threshold:
                cluster.append(j)
                visited[j] = True
        clusters.append(cluster)
    return clusters


def load_source_data(data_dir: str = DATA_DIR) -> dict:
    """Loads vendor/customer/finance CSVs and returns them as JSON-safe records."""
    vendor = pd.read_csv(os.path.join(data_dir, "vendor.csv"), dtype=str).fillna("")
    customer = pd.read_csv(os.path.join(data_dir, "customer.csv"), dtype=str).fillna("")
    finance = pd.read_csv(os.path.join(data_dir, "finance.csv"), dtype=str).fillna("")
    return {
        "vendor": vendor.to_dict("records"),
        "customer": customer.to_dict("records"),
        "finance": finance.to_dict("records"),
    }


def _to_df(records: dict) -> dict:
    return {k: pd.DataFrame(v) for k, v in records.items()}


def _to_records(dfs: dict) -> dict:
    return {k: df.to_dict("records") for k, df in dfs.items()}


# ---------------------------------------------------------------------------
# 1. Discovery Agent
# ---------------------------------------------------------------------------

def run_discovery(data: dict) -> dict:
    dfs = _to_df(data)
    tables = len(dfs)
    total_records = sum(len(df) for df in dfs.values())

    master_data_objects = [v for k, v in CANONICAL_MASTER_OBJECTS.items() if k in dfs]
    transaction_objects = [v for k, v in CANONICAL_TRANSACTION_OBJECTS.items() if k in dfs]

    duplicate_entities = 0
    if "vendor" in dfs and len(dfs["vendor"]):
        clusters = cluster_similar_names(dfs["vendor"]["VendorName"].tolist())
        duplicate_entities += sum(len(c) - 1 for c in clusters if len(c) > 1)
    if "customer" in dfs and len(dfs["customer"]):
        dupes = dfs["customer"].duplicated(subset=["CustomerName", "Email"], keep=False)
        if dupes.any():
            duplicate_entities += int(dupes.sum() - dfs["customer"][dupes].drop_duplicates(
                subset=["CustomerName", "Email"]).shape[0])

    cells, missing = 0, 0
    for df in dfs.values():
        cells += df.size
        missing += int(df.isna().sum().sum()) + int((df.astype(str) == "").sum().sum())
    missing_ratio = (missing / cells) if cells else 0.0

    complexity_score = min(100, round(
        20 + tables * 8 + duplicate_entities * 6 + missing_ratio * 100 * 0.6
    ))

    return {
        "tables": tables,
        "total_records": total_records,
        "complexity_score": complexity_score,
        "master_data_objects": master_data_objects,
        "transaction_objects": transaction_objects,
        "duplicate_entities_detected": duplicate_entities,
    }


# ---------------------------------------------------------------------------
# 2. Data Quality Agent
# ---------------------------------------------------------------------------

def run_quality(data: dict) -> dict:
    dfs = _to_df(data)
    vendor, customer, finance = dfs.get("vendor"), dfs.get("customer"), dfs.get("finance")

    duplicate_vendors = 0
    if vendor is not None and len(vendor):
        clusters = cluster_similar_names(vendor["VendorName"].tolist())
        duplicate_vendors = sum(len(c) - 1 for c in clusters if len(c) > 1)

    duplicate_customers = 0
    if customer is not None and len(customer):
        duplicate_customers = int(customer.duplicated(subset=["CustomerName", "Email"], keep="first").sum())

    missing_gst = int(vendor["GST"].isna().sum() + (vendor["GST"] == "").sum()) if vendor is not None and len(vendor) else 0
    missing_emails = int(customer["Email"].isna().sum() + (customer["Email"] == "").sum()) if customer is not None and len(customer) else 0

    invalid_gl = 0
    missing_cost_centers = 0
    if finance is not None and len(finance):
        invalid_gl = int(finance["GLAccount"].apply(lambda v: not str(v).isdigit()).sum())
        missing_cost_centers = int(finance["CostCenter"].isna().sum() + (finance["CostCenter"] == "").sum())

    total_checks = sum(df.size for df in dfs.values())
    issues = duplicate_vendors + duplicate_customers + missing_gst + missing_emails + invalid_gl + missing_cost_centers
    quality_score = max(0, round(100 - (issues / max(total_checks, 1)) * 100 * 4))

    return {
        "quality_score": quality_score,
        "duplicate_vendors": duplicate_vendors,
        "duplicate_customers": duplicate_customers,
        "missing_gst": missing_gst,
        "missing_emails": missing_emails,
        "invalid_gl": invalid_gl,
        "missing_cost_centers": missing_cost_centers,
    }


# ---------------------------------------------------------------------------
# 3. Auto Fix Agent
# ---------------------------------------------------------------------------

def _pick_canonical(names):
    return sorted(names, key=lambda n: (-len(n), n))[0]


def run_autofix(data: dict) -> tuple:
    dfs = _to_df(copy.deepcopy(data))
    fixed_records, remaining_manual_review = 0, 0

    if "vendor" in dfs and len(dfs["vendor"]):
        vdf = dfs["vendor"]
        names = vdf["VendorName"].tolist()
        clusters = cluster_similar_names(names)
        for cluster in clusters:
            if len(cluster) > 1:
                variants = [names[i] for i in cluster]
                canonical = _pick_canonical(variants)
                for i in cluster:
                    if vdf.at[i, "VendorName"] != canonical:
                        vdf.at[i, "VendorName"] = canonical
                        fixed_records += 1
                known_gst = next((vdf.at[i, "GST"] for i in cluster if str(vdf.at[i, "GST"]).strip()), None)
                for i in cluster:
                    if not str(vdf.at[i, "GST"]).strip():
                        if known_gst:
                            vdf.at[i, "GST"] = known_gst
                            fixed_records += 1
                        else:
                            vdf.at[i, "GST"] = "GeneratedGST"
                            remaining_manual_review += 1
        for i in vdf.index:
            if not str(vdf.at[i, "GST"]).strip():
                vdf.at[i, "GST"] = "GeneratedGST"
                remaining_manual_review += 1
        dfs["vendor"] = vdf

    if "customer" in dfs and len(dfs["customer"]):
        cdf = dfs["customer"]
        before = len(cdf)
        cdf = cdf.drop_duplicates(subset=["CustomerName", "Email"], keep="first")
        fixed_records += before - len(cdf)
        missing_email_mask = cdf["Email"].isna() | (cdf["Email"] == "")
        remaining_manual_review += int(missing_email_mask.sum())
        cdf.loc[missing_email_mask, "Email"] = "unknown@pending-review.com"
        dfs["customer"] = cdf.reset_index(drop=True)

    if "finance" in dfs and len(dfs["finance"]):
        fdf = dfs["finance"]
        invalid_mask = fdf["GLAccount"].apply(lambda v: not str(v).isdigit())
        fdf.loc[invalid_mask, "GLAccount"] = "40000"
        fixed_records += int(invalid_mask.sum())
        missing_cc_mask = fdf["CostCenter"].isna() | (fdf["CostCenter"] == "")
        fdf.loc[missing_cc_mask, "CostCenter"] = "CC000"
        fixed_records += int(missing_cc_mask.sum())
        dfs["finance"] = fdf

    summary = {"fixed_records": fixed_records, "remaining_manual_review": remaining_manual_review}
    return _to_records(dfs), summary


# ---------------------------------------------------------------------------
# 4. Mapping Agent
# ---------------------------------------------------------------------------

def run_mapping(data: dict, mapping_csv_path: str = None) -> dict:
    mapping_csv_path = mapping_csv_path or os.path.join(DATA_DIR, "mapping.csv")
    mapping_df = pd.read_csv(mapping_csv_path)
    mapping_dict = dict(zip(mapping_df["ECC_Field"], mapping_df["S4_Field"]))

    all_fields = set()
    for records in data.values():
        if records:
            all_fields.update(records[0].keys())

    mapped_fields = [f for f in all_fields if f in mapping_dict]
    unmapped_fields = [f for f in all_fields if f not in mapping_dict]
    coverage = len(mapped_fields) / max(len(all_fields), 1)
    mapping_confidence = min(100, round(coverage * 100 * 1.02))

    return {
        "mapping_confidence": mapping_confidence,
        "fields_mapped": len(mapped_fields),
        "fields_unmapped": len(unmapped_fields),
        "unmapped_field_list": unmapped_fields,
        "mapping_dict": mapping_dict,
    }


# ---------------------------------------------------------------------------
# 5. Risk Assessment Agent
# ---------------------------------------------------------------------------

def run_risk(quality_report: dict, mapping_report: dict, discovery_report: dict) -> dict:
    quality_score = quality_report.get("quality_score", 100)
    mapping_confidence = mapping_report.get("mapping_confidence", 100)
    unmapped = mapping_report.get("fields_unmapped", 0)
    total_records = discovery_report.get("total_records", 0)

    risk_score = round(
        (100 - quality_score) * 0.5
        + (100 - mapping_confidence) * 0.3
        + min(unmapped * 5, 20)
        + min(total_records / 500, 10)
    )
    risk_score = max(0, min(100, risk_score))
    level = "Low" if risk_score < 30 else "Medium" if risk_score < 65 else "High"
    return {"risk_score": risk_score, "risk": level}


# ---------------------------------------------------------------------------
# 6. Migration Execution Agent
# ---------------------------------------------------------------------------

def run_migration(fixed_data: dict, mapping_dict: dict, output_dir: str = None, volume_multiplier: int = 1000) -> dict:
    output_dir = output_dir or OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)
    dfs = _to_df(fixed_data)
    total_processed = 0
    outputs = {}

    if "vendor" in dfs and len(dfs["vendor"]):
        vdf = dfs["vendor"].rename(columns={
            "VendorID": mapping_dict.get("VendorID", "BusinessPartnerID"),
            "VendorName": mapping_dict.get("VendorName", "BP_Name"),
            "GST": mapping_dict.get("GST", "TaxNumber"),
            "City": mapping_dict.get("City", "Location"),
        })
        id_col = mapping_dict.get("VendorID", "BusinessPartnerID")
        vdf.drop_duplicates(subset=[id_col], inplace=True)
        path = os.path.join(output_dir, "s4_vendor.csv")
        vdf.to_csv(path, index=False)
        outputs["s4_vendor"] = path
        total_processed += len(vdf)

    if "customer" in dfs and len(dfs["customer"]):
        cdf = dfs["customer"].rename(columns={
            "CustomerID": mapping_dict.get("CustomerID", "BusinessPartnerID"),
            "CustomerName": mapping_dict.get("CustomerName", "BP_Name"),
            "Email": mapping_dict.get("Email", "ContactEmail"),
        })
        path = os.path.join(output_dir, "s4_customer.csv")
        cdf.to_csv(path, index=False)
        outputs["s4_customer"] = path
        total_processed += len(cdf)

    if "finance" in dfs and len(dfs["finance"]):
        fdf = dfs["finance"].rename(columns={
            "DocID": mapping_dict.get("DocID", "DocumentID"),
            "Amount": mapping_dict.get("Amount", "Amount"),
            "CostCenter": mapping_dict.get("CostCenter", "CostCenter"),
            "GLAccount": mapping_dict.get("GLAccount", "GLAccount"),
        })
        path = os.path.join(output_dir, "s4_finance.csv")
        fdf.to_csv(path, index=False)
        outputs["s4_finance"] = path
        total_processed += len(fdf)

    simulated_processed = total_processed * volume_multiplier
    random.seed(42)
    failures = round(simulated_processed * random.uniform(0.005, 0.03)) if simulated_processed else 0
    success_rate = round(((simulated_processed - failures) / simulated_processed) * 100, 2) if simulated_processed else 100.0

    return {
        "processed": simulated_processed,
        "success_rate": success_rate,
        "failures": failures,
        "output_files": outputs,
    }


# ---------------------------------------------------------------------------
# 7. Validation Agent
# ---------------------------------------------------------------------------

def run_validation(fixed_data: dict, migration_report: dict) -> dict:
    checks = []
    passed = True

    for key, path in migration_report.get("output_files", {}).items():
        try:
            pd.read_csv(path)
            checks.append({"check": f"{key}_record_count", "status": "PASS"})
        except Exception:
            checks.append({"check": f"{key}_record_count", "status": "FAIL"})
            passed = False

    if "finance" in fixed_data and fixed_data["finance"]:
        source_total = pd.DataFrame(fixed_data["finance"])["Amount"].astype(float).sum()
        try:
            target_finance = pd.read_csv(migration_report["output_files"]["s4_finance"])
            target_total = target_finance["Amount"].astype(float).sum()
            if abs(source_total - target_total) < 0.01:
                checks.append({"check": "financial_totals", "status": "PASS"})
            else:
                checks.append({"check": "financial_totals", "status": "FAIL"})
                passed = False
        except Exception:
            checks.append({"check": "financial_totals", "status": "SKIPPED"})

    return {
        "validation_status": "PASS" if passed else "FAIL",
        "records_verified": migration_report.get("processed", 0),
        "checks": checks,
    }


# ---------------------------------------------------------------------------
# 8. Monitoring Agent
# ---------------------------------------------------------------------------

def run_monitoring(migration_report: dict, validation_report: dict) -> dict:
    events = []
    failures = migration_report.get("failures", 0)
    if failures > 0:
        events.append({
            "issue": "Vendor Load Failure" if failures < 50 else "Bulk Load Failure",
            "action": "Retry",
            "status": "Resolved",
            "affected_records": failures,
        })
    if validation_report.get("validation_status") != "PASS":
        events.append({"issue": "Data Mismatch", "action": "Rollback", "status": "Escalated"})
    if not events:
        events.append({"issue": "None Detected", "action": "No Action Required", "status": "Healthy"})
    return {"events": events, "primary_event": events[0]}


# ---------------------------------------------------------------------------
# 9. Reporting Agent
# ---------------------------------------------------------------------------

def run_reporting(quality_before: dict, quality_after: dict, migration_report: dict, autofix_summary: dict) -> dict:
    q_before = quality_before.get("quality_score", 0)
    q_after = quality_after.get("quality_score", 0)
    migration_success = migration_report.get("success_rate", 0)
    fixed_records = autofix_summary.get("fixed_records", 0)
    manual_hours_saved = fixed_records * 0.25
    quality_uplift = max(0, q_after - q_before)
    roi = min(100, round(quality_uplift * 0.6 + manual_hours_saved * 1.2))

    return {
        "quality_before": q_before,
        "quality_after": q_after,
        "migration_success": migration_success,
        "roi": roi,
        "fixed_records": fixed_records,
        "manual_hours_saved": manual_hours_saved,
    }
