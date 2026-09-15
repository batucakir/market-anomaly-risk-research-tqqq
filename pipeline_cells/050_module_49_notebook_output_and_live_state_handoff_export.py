# ==============================================================================
# MODULE 49 — NOTEBOOK OUTPUT AND LIVE-STATE HANDOFF EXPORT
# ==============================================================================
# Save the notebook before running this final module. It creates one ZIP file
# containing the saved notebook outputs and the current kernel's result state.
# No model, price, target, parameter, checkpoint, or result is modified.

import csv
import hashlib
import json
import os
import platform
import shutil
import sys
import zipfile
from datetime import date, datetime
from pathlib import Path

import numpy as np
import pandas as pd


M49_EXPORT_VERSION = "1.0"
M49_MAX_FULL_TABLE_ROWS = 100_000
M49_MAX_FULL_TABLE_BYTES = 30_000_000
M49_PREVIEW_ROWS = 250


def m49_safe_filename(value):
    text = "".join(
        character if character.isalnum() or character in "._-" else "_"
        for character in str(value)
    ).strip("._")
    return text[:180] or "unnamed"


def m49_json_value(value):
    if value is None or isinstance(value, (str, bool, int, float)):
        if isinstance(value, float) and not np.isfinite(value):
            return str(value)
        return value
    if isinstance(value, np.generic):
        return m49_json_value(value.item())
    if isinstance(value, (pd.Timestamp, datetime, date)):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (list, tuple)):
        if len(value) > 500:
            return {"type": type(value).__name__, "length": len(value)}
        return [m49_json_value(item) for item in value]
    if isinstance(value, dict):
        if len(value) > 500:
            return {"type": "dict", "length": len(value)}
        result = {}
        for key, item in value.items():
            if isinstance(item, (pd.DataFrame, pd.Series, np.ndarray)):
                result[str(key)] = {
                    "type": type(item).__name__,
                    "shape": list(getattr(item, "shape", (len(item),))),
                }
            else:
                result[str(key)] = m49_json_value(item)
        return result
    return str(value)


def m49_relevant_name(name):
    upper = str(name).upper()
    prefixes = (
        "V4", "V5", "V6", "V7", "V8", "V9", "V10", "V11", "V12",
        "V13", "V14", "V15", "V16", "BLOCK", "B38", "B39", "B40",
        "B41", "B42", "RESTORE", "ALL_VERSION", "REPORT",
    )
    exact = {
        "EVENT_COMPARE", "SUMMARY", "YEARLY_ROWS", "FAILURE_RATES",
        "PORTFOLIO_LEADER", "TCA_RATE", "BASE_TCA_RATE",
    }
    return upper.startswith(prefixes) or upper in exact


def m49_result_table_name(name):
    upper = str(name).upper()
    keywords = (
        "SUMMARY", "RESULT", "PATH", "AUDIT", "VERDICT", "STATUS",
        "PERFORMANCE", "YEARLY", "ROBUSTNESS", "CONTRIBUT", "EVENT",
        "WEALTH", "COVERAGE", "PREFLIGHT", "RANKING", "DRAWDOWN",
        "SCORE", "DECISION", "COMPARISON", "REPORT", "FREEZE",
    )
    return m49_relevant_name(name) and any(word in upper for word in keywords)


def m49_frame_bytes(frame):
    try:
        return int(frame.memory_usage(index=True, deep=True).sum())
    except Exception:
        return -1


def m49_write_frame(name, frame, table_dir, manifest_rows):
    clean_name = m49_safe_filename(name)
    if isinstance(frame, pd.Series):
        output = frame.rename("Value").to_frame()
    else:
        output = frame
    rows, columns = output.shape
    memory_bytes = m49_frame_bytes(output)
    full = (
        rows <= M49_MAX_FULL_TABLE_ROWS
        and (memory_bytes < 0 or memory_bytes <= M49_MAX_FULL_TABLE_BYTES)
    )
    if full:
        export = output
        status = "FULL"
        filename = clean_name + ".csv"
    else:
        preview_rows = min(M49_PREVIEW_ROWS, rows)
        export = pd.concat(
            [output.head(preview_rows), output.tail(preview_rows)]
        ).drop_duplicates()
        status = "HEAD_TAIL_PREVIEW"
        filename = clean_name + "__preview.csv"
    path = table_dir / filename
    export.to_csv(path, index=True)
    manifest_rows.append({
        "Name": name,
        "Type": type(frame).__name__,
        "Rows": int(rows),
        "Columns": int(columns),
        "Memory_Bytes": memory_bytes,
        "Export_Status": status,
        "File": str(path.relative_to(table_dir.parent)),
    })


def m49_candidate_notebooks(namespace):
    candidates = []
    direct_names = (
        "__vsc_ipynb_file__", "__notebook_path__", "NOTEBOOK_PATH",
        "IPYNB_PATH",
    )
    for name in direct_names:
        value = namespace.get(name)
        if value:
            path = Path(str(value)).expanduser()
            if path.is_file() and path.suffix.lower() == ".ipynb":
                candidates.append((1_000_000_000_000, path.resolve(), name))

    if candidates:
        return sorted(candidates, key=lambda item: (item[0], str(item[1])), reverse=True)

    session_name = os.environ.get("JPY_SESSION_NAME")
    if session_name:
        path = Path(session_name).expanduser()
        if not path.is_absolute():
            path = Path.cwd() / path
        if path.is_file() and path.suffix.lower() == ".ipynb":
            candidates.append((900_000_000_000, path.resolve(), "JPY_SESSION_NAME"))

    if candidates:
        return sorted(candidates, key=lambda item: (item[0], str(item[1])), reverse=True)

    search_roots = [Path.cwd(), Path.home() / "Downloads"]
    seen = set()
    for root in search_roots:
        if not root.is_dir():
            continue
        for path in root.glob("*.ipynb"):
            try:
                resolved = path.resolve()
                if resolved in seen:
                    continue
                seen.add(resolved)
                text = path.read_text(encoding="utf-8", errors="replace")
                score = 0
                for marker, points in (
                    ("MODULE 48", 500), ("ALL VERSIONS", 250),
                    ("V16", 100), ("V12", 50), ("V8", 25),
                ):
                    if marker in text:
                        score += points
                score += int(path.stat().st_mtime // 60) % 100_000
                candidates.append((score, resolved, "AUTO_SEARCH"))
            except Exception:
                continue
    return sorted(candidates, key=lambda item: (item[0], str(item[1])), reverse=True)


def m49_extract_saved_outputs(notebook, destination):
    lines = []
    code_cells = 0
    executed_cells = 0
    output_blocks = 0
    saved_errors = []
    for cell_number, cell in enumerate(notebook.get("cells", []), start=1):
        if cell.get("cell_type") != "code":
            continue
        code_cells += 1
        execution_count = cell.get("execution_count")
        outputs = cell.get("outputs", [])
        if execution_count is not None:
            executed_cells += 1
        if not outputs:
            continue
        source = "".join(cell.get("source", []))
        first_line = next((line.strip() for line in source.splitlines() if line.strip()), "")
        lines.append("=" * 120)
        lines.append(
            "CELL {} | execution_count={} | {}".format(
                cell_number, execution_count, first_line[:180]
            )
        )
        lines.append("=" * 120)
        for output_number, output in enumerate(outputs, start=1):
            output_blocks += 1
            output_type = output.get("output_type", "unknown")
            lines.append("\n[OUTPUT {} | {}]".format(output_number, output_type))
            if output_type == "stream":
                lines.append("".join(output.get("text", [])))
            elif output_type == "error":
                error = {
                    "cell": cell_number,
                    "execution_count": execution_count,
                    "ename": output.get("ename"),
                    "evalue": output.get("evalue"),
                    "traceback": output.get("traceback", []),
                }
                saved_errors.append(error)
                lines.append("{}: {}".format(error["ename"], error["evalue"]))
                lines.extend(error["traceback"])
            elif output_type in ("display_data", "execute_result"):
                data = output.get("data", {})
                if "text/plain" in data:
                    lines.append("".join(data["text/plain"]))
                elif "text/html" in data:
                    lines.append("[HTML output present in notebook snapshot]")
                else:
                    lines.append(
                        "[Embedded output MIME types: {}]".format(
                            ", ".join(sorted(data))
                        )
                    )
            else:
                lines.append(m49_json_value(output))
        lines.append("")
    destination.write_text("\n".join(lines), encoding="utf-8")
    return {
        "code_cells": code_cells,
        "executed_code_cells": executed_cells,
        "output_blocks": output_blocks,
        "saved_error_count": len(saved_errors),
        "saved_errors": saved_errors,
    }


print("=" * 120)
print("MODULE 49 — NOTEBOOK OUTPUT AND LIVE-STATE HANDOFF EXPORT")
print("=" * 120)

M49_NAMESPACE = globals()
M49_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
M49_EXPORT_ROOT = Path.cwd() / ("notebook_handoff_" + M49_TIMESTAMP)
M49_TABLE_DIR = M49_EXPORT_ROOT / "tables"
M49_REGISTRY_DIR = M49_EXPORT_ROOT / "version_registry"
M49_EXPORT_ROOT.mkdir(parents=True, exist_ok=False)
M49_TABLE_DIR.mkdir()
M49_REGISTRY_DIR.mkdir()

M49_NOTEBOOK_CANDIDATES = m49_candidate_notebooks(M49_NAMESPACE)
M49_NOTEBOOK_PATH = M49_NOTEBOOK_CANDIDATES[0][1] if M49_NOTEBOOK_CANDIDATES else None
M49_NOTEBOOK_SOURCE = M49_NOTEBOOK_CANDIDATES[0][2] if M49_NOTEBOOK_CANDIDATES else None
M49_NOTEBOOK_AUDIT = {
    "detected": M49_NOTEBOOK_PATH is not None,
    "path": str(M49_NOTEBOOK_PATH) if M49_NOTEBOOK_PATH else None,
    "detection_source": M49_NOTEBOOK_SOURCE,
    "candidate_count": len(M49_NOTEBOOK_CANDIDATES),
    "warning": (
        "The snapshot contains only outputs saved before Module 49 was run."
        if M49_NOTEBOOK_PATH
        else "No notebook file was detected; live-state exports are still included."
    ),
}

M49_SAVED_OUTPUT_AUDIT = None
if M49_NOTEBOOK_PATH is not None:
    M49_NOTEBOOK_COPY = M49_EXPORT_ROOT / "executed_notebook_snapshot.ipynb"
    shutil.copy2(M49_NOTEBOOK_PATH, M49_NOTEBOOK_COPY)
    with M49_NOTEBOOK_COPY.open("r", encoding="utf-8") as handle:
        M49_NOTEBOOK_JSON = json.load(handle)
    M49_SAVED_OUTPUT_AUDIT = m49_extract_saved_outputs(
        M49_NOTEBOOK_JSON, M49_EXPORT_ROOT / "notebook_outputs.txt"
    )

M49_SCALARS = {}
M49_OBJECT_MANIFEST = []
M49_TABLE_MANIFEST = []
M49_TABLE_EXPORT_ERRORS = []

for M49_NAME, M49_VALUE in sorted(list(M49_NAMESPACE.items())):
    if M49_NAME.startswith("_") or M49_NAME.startswith("M49_"):
        continue
    if not m49_relevant_name(M49_NAME):
        continue
    shape = getattr(M49_VALUE, "shape", None)
    M49_OBJECT_MANIFEST.append({
        "Name": M49_NAME,
        "Type": type(M49_VALUE).__name__,
        "Shape": list(shape) if shape is not None else None,
    })
    if isinstance(M49_VALUE, (str, bool, int, float, np.generic,
                              pd.Timestamp, datetime, date, Path)):
        M49_SCALARS[M49_NAME] = m49_json_value(M49_VALUE)
    elif isinstance(M49_VALUE, (list, tuple, dict)):
        M49_SCALARS[M49_NAME] = m49_json_value(M49_VALUE)
    if isinstance(M49_VALUE, (pd.DataFrame, pd.Series)) and m49_result_table_name(M49_NAME):
        try:
            m49_write_frame(
                M49_NAME, M49_VALUE.copy(deep=True),
                M49_TABLE_DIR, M49_TABLE_MANIFEST
            )
        except Exception as error:
            M49_TABLE_EXPORT_ERRORS.append({
                "Name": M49_NAME,
                "Error": type(error).__name__ + ": " + str(error),
            })

M49_REGISTRY_SUMMARY = []
if isinstance(M49_NAMESPACE.get("RESTORED_VERSION_RESULTS"), dict):
    for version, result in M49_NAMESPACE["RESTORED_VERSION_RESULTS"].items():
        if not isinstance(result, dict):
            continue
        M49_REGISTRY_SUMMARY.append({
            "Version": version,
            "Final_Wealth": m49_json_value(result.get("final_wealth")),
            "First_Execution": m49_json_value(result.get("first_execution")),
            "End": m49_json_value(result.get("end")),
            "Accounting": m49_json_value(result.get("basis")),
            "Historical_Status": m49_json_value(result.get("historical_status")),
            "Current_Status": m49_json_value(result.get("current_status")),
        })
        marks = result.get("marks")
        if isinstance(marks, pd.DataFrame):
            marks.copy(deep=True).to_csv(
                M49_REGISTRY_DIR / (m49_safe_filename(version) + "__marks.csv"),
                index=False,
            )

(M49_EXPORT_ROOT / "live_scalars.json").write_text(
    json.dumps(M49_SCALARS, indent=2, ensure_ascii=False, default=str),
    encoding="utf-8",
)
pd.DataFrame(M49_OBJECT_MANIFEST).to_csv(
    M49_EXPORT_ROOT / "live_objects_manifest.csv", index=False
)
pd.DataFrame(M49_TABLE_MANIFEST).to_csv(
    M49_EXPORT_ROOT / "table_export_manifest.csv", index=False
)
pd.DataFrame(M49_REGISTRY_SUMMARY).to_csv(
    M49_EXPORT_ROOT / "version_registry_summary.csv", index=False
)

M49_ENVIRONMENT = {
    "export_version": M49_EXPORT_VERSION,
    "created_at_local": datetime.now().isoformat(),
    "python": sys.version,
    "platform": platform.platform(),
    "executable": sys.executable,
    "working_directory": str(Path.cwd()),
    "numpy": np.__version__,
    "pandas": pd.__version__,
}
for package_name in ("sklearn", "scipy", "cvxpy", "yfinance", "matplotlib"):
    try:
        package = __import__(package_name)
        M49_ENVIRONMENT[package_name] = getattr(package, "__version__", "unknown")
    except Exception as error:
        M49_ENVIRONMENT[package_name] = "unavailable: " + type(error).__name__

M49_EXPORT_AUDIT = {
    "environment": M49_ENVIRONMENT,
    "notebook": M49_NOTEBOOK_AUDIT,
    "saved_outputs": M49_SAVED_OUTPUT_AUDIT,
    "live_relevant_objects": len(M49_OBJECT_MANIFEST),
    "exported_result_tables": len(M49_TABLE_MANIFEST),
    "table_export_errors": M49_TABLE_EXPORT_ERRORS,
    "version_registry_entries": len(M49_REGISTRY_SUMMARY),
}
(M49_EXPORT_ROOT / "export_audit.json").write_text(
    json.dumps(M49_EXPORT_AUDIT, indent=2, ensure_ascii=False, default=str),
    encoding="utf-8",
)

M49_README = """Notebook handoff package

Upload the ZIP file created beside this folder. It contains:
- the detected saved notebook, including its stored cell outputs;
- plain-text extraction of saved outputs and tracebacks;
- current-kernel V4–V16/BLOCK result scalars and object inventory;
- result, path, audit, coverage, performance and comparison tables;
- independent version-registry wealth marks;
- Python and package versions.

Large non-result research panels are inventoried but not copied in full.
No model, price, target, checkpoint, parameter, or result was changed.
"""
(M49_EXPORT_ROOT / "README.txt").write_text(M49_README, encoding="utf-8")

M49_ZIP_PATH = M49_EXPORT_ROOT.with_suffix(".zip")
with zipfile.ZipFile(M49_ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    for file in sorted(M49_EXPORT_ROOT.rglob("*")):
        if file.is_file():
            archive.write(file, file.relative_to(M49_EXPORT_ROOT.parent))

M49_ZIP_HASHER = hashlib.sha256()
with M49_ZIP_PATH.open("rb") as handle:
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
        M49_ZIP_HASHER.update(chunk)
M49_ZIP_SHA256 = M49_ZIP_HASHER.hexdigest()
print("\n[+] Handoff export complete.")
print("ZIP FILE :", M49_ZIP_PATH.resolve())
print("SHA256   :", M49_ZIP_SHA256)
print("NOTEBOOK :", M49_NOTEBOOK_PATH if M49_NOTEBOOK_PATH else "NOT DETECTED")
print("TABLES   :", len(M49_TABLE_MANIFEST))
print("VERSIONS :", len(M49_REGISTRY_SUMMARY))
if M49_NOTEBOOK_PATH is None:
    print("[!] Upload is usable, but saved cell outputs are absent because the notebook file was not detected.")
else:
    print("[+] Upload the generated ZIP file in this chat.")
