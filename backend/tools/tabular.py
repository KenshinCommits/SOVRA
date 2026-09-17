import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
import pandas as pd

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent

def _is_safe_path(target_path: str) -> bool:
    try:
        abs_path = (WORKSPACE_ROOT / target_path).resolve()
        return str(abs_path).startswith(str(WORKSPACE_ROOT))
    except Exception:
        return False

def exec_analyze_tabular_data(
    file_path: str,
    calculation_type: str = "summary",
    threshold_col: Optional[str] = None,
    threshold_val: Optional[float] = None
) -> str:
    """
    Deterministically inspects and calculates statistics on CSV or XLSX telemetry datasets.
    Computes exact aggregates (mean, min, max, std, count) and detects threshold violations.
    Prevents LLM arithmetic hallucinations.
    """
    if not _is_safe_path(file_path):
        return f"Error: Access denied. Path '{file_path}' is outside the allowed workspace."

    abs_path = (WORKSPACE_ROOT / file_path).resolve()
    if not abs_path.exists():
        return f"Error: File '{file_path}' does not exist."
    if not abs_path.is_file():
        return f"Error: Path '{file_path}' is not a file."

    ext = abs_path.suffix.lower()
    if ext not in [".csv", ".xlsx", ".xls"]:
        return f"Error: Unsupported tabular format '{ext}'. Supported: .csv, .xlsx, .xls"

    try:
        if ext == ".csv":
            df = pd.read_csv(abs_path)
        else:
            df = pd.read_excel(abs_path)

        if df.empty:
            return f"Error: The dataset in '{file_path}' contains zero records."

        total_rows = len(df)
        columns = list(df.columns)
        numeric_cols = list(df.select_dtypes(include=["number"]).columns)

        report_lines = [
            f"[Deterministic Tabular Analysis: {abs_path.name}]",
            "Classification: SYNTHETIC DEMO DATASET (Validation Telemetry)",
            f"Total Records: {total_rows} rows | Columns ({len(columns)}): {', '.join(columns)}",
            "---"
        ]

        # 1. Summary statistics for all numeric columns
        stats_summary = {}
        for col in numeric_cols:
            col_series = df[col].dropna()
            if not col_series.empty:
                c_min = float(col_series.min())
                c_max = float(col_series.max())
                c_mean = float(col_series.mean())
                c_std = float(col_series.std()) if len(col_series) > 1 else 0.0
                stats_summary[col] = {
                    "count": int(len(col_series)),
                    "min": round(c_min, 4),
                    "max": round(c_max, 4),
                    "mean": round(c_mean, 4),
                    "std": round(c_std, 4)
                }
                report_lines.append(
                    f"Column '{col}': mean={c_mean:.2f}, min={c_min:.2f}, max={c_max:.2f}, std={c_std:.2f}"
                )

        # 2. Specific threshold check
        if threshold_col and threshold_val is not None:
            if threshold_col not in df.columns:
                report_lines.append(f"Warning: Specified threshold column '{threshold_col}' not found in dataset.")
            else:
                exceedances = df[df[threshold_col] > threshold_val]
                exc_count = len(exceedances)
                exc_pct = (exc_count / total_rows) * 100.0
                report_lines.append("---")
                report_lines.append(
                    f"Threshold Audit: '{threshold_col}' > {threshold_val} | "
                    f"Violations: {exc_count} / {total_rows} ({exc_pct:.1f}%)"
                )
                if exc_count > 0:
                    sample_timestamps = exceedances['timestamp'].head(3).tolist() if 'timestamp' in exceedances else []
                    if sample_timestamps:
                        report_lines.append(f"First violation timestamps: {', '.join(str(t) for t in sample_timestamps)}")

        # 3. Known Engineering threshold checks if columns match standard telemetry
        eng_limits = {
            "vibration_rms_mms": (4.5, "Alarm Limit: 4.5 mm/s"),
            "bearing_temp_c": (75.0, "Max Steady State: 75.0 C"),
            "leakage_rate_dpm": (5.0, "Allowable Leakage: 5 dpm")
        }
        detected_anomalies = []
        for ecol, (elimit, edesc) in eng_limits.items():
            if ecol in df.columns:
                viol = df[df[ecol] > elimit]
                if not viol.empty:
                    detected_anomalies.append(f"{ecol} exceeded {edesc} in {len(viol)} instances (Peak: {viol[ecol].max():.2f})")

        if detected_anomalies:
            report_lines.append("---")
            report_lines.append("AUTOMATED ENGINEERING RULE AUDIT:")
            for anom in detected_anomalies:
                report_lines.append(f"- {anom}")

        return "\n".join(report_lines)

    except Exception as e:
        return f"Error analyzing tabular dataset: {str(e)}"
