# ==============================================================================
# MODULE 14 — HISTORICAL BLOCK 38A
# FINAL PITINDEX PYTHON 3.11 BRIDGE
# ==============================================================================
#
# Historical restoration note:
#
# The original Block 38A derived V4_COMPARISON_START and V4_DATA_END_DATE
# from block28_panel.
#
# The old kernel is gone, but the exact historical boundaries are recovered
# from the frozen V3 long-history lineage:
#
#     V4_COMPARISON_START = 2023-10-10
#     V4_DATA_END_DATE    = 2026-07-27
#
# No model rule, universe rule, parameter or research boundary is changed.
#
# Existing historical PIT cache is reused when available to prevent
# external-data version drift.
# ==============================================================================

import sys
import os
import shutil
import subprocess
import tempfile

from pathlib import Path

import pandas as pd


print("=" * 100)
print("MODULE 14 / HISTORICAL BLOCK 38A — FINAL PITINDEX PYTHON 3.11 BRIDGE")
print("=" * 100)

print(
    "\nNotebook Python:",
    sys.version.splitlines()[0],
)


# ==============================================================================
# 0. UPSTREAM INTEGRITY GATE
# ==============================================================================

EXPECTED_V4_MASTER_FINGERPRINT = (
    "7f2b6040db974ee5d1df151d9fa49cab"
    "79dea945cd5fe19d442821a35b7c7bd8"
)


if "V4_MASTER_FINGERPRINT" not in globals():

    raise RuntimeError(
        "MODULE 14 requires MODULE 13 first."
    )


if (
    V4_MASTER_FINGERPRINT
    !=
    EXPECTED_V4_MASTER_FINGERPRINT
):

    raise RuntimeError(
        "\nHISTORICAL V4 MASTER FINGERPRINT MISMATCH.\n"
        f"Expected: {EXPECTED_V4_MASTER_FINGERPRINT}\n"
        f"Actual  : {V4_MASTER_FINGERPRINT}\n"
        "STOP. Do not continue."
    )


# ==============================================================================
# 1. EXACT HISTORICAL PROJECT DATES
# ==============================================================================

V4_COMPARISON_START = pd.Timestamp(
    "2023-10-10"
)

V4_DATA_END_DATE = pd.Timestamp(
    "2026-07-27"
)


# Runtime history established 2021-03-31 as the usable SP1500 composite floor
# for the final isolated-pitindex bridge used by the historical project.

B38_PIT_START_DATE = pd.Timestamp(
    "2021-03-31"
)


print(
    "\nPIT start       :",
    B38_PIT_START_DATE.date(),
)

print(
    "Comparison start:",
    V4_COMPARISON_START.date(),
)

print(
    "Research end    :",
    V4_DATA_END_DATE.date(),
)


# ==============================================================================
# 2. OUTPUT PATHS
# ==============================================================================

cache_dir = Path(
    "./v4_cache"
)

cache_dir.mkdir(
    parents=True,
    exist_ok=True,
)


B38_PIT_BRIDGE_CSV = (
    cache_dir
    /
    "block38_sp1500_pit_history_FINAL.csv"
)


B38_PIT_INFO_TXT = (
    cache_dir
    /
    "block38_pitindex_info_FINAL.txt"
)


# ==============================================================================
# 3. HISTORICAL CACHE-FIRST RECOVERY
# ==============================================================================

B38A_REUSED_HISTORICAL_CACHE = (
    B38_PIT_BRIDGE_CSV.exists()
)


if B38A_REUSED_HISTORICAL_CACHE:

    print(
        "\n[38A] Reusing historical PIT bridge cache:"
    )

    print(
        B38_PIT_BRIDGE_CSV
    )


else:

    # ==========================================================================
    # 4. ENSURE UV EXISTS
    # ==========================================================================

    uv_exe = shutil.which(
        "uv"
    )


    if uv_exe is None:

        print(
            "\n[38A] Installing uv..."
        )

        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-q",
                "uv",
            ]
        )

        uv_exe = shutil.which(
            "uv"
        )


    if uv_exe is None:

        candidate = (
            Path(
                sys.executable
            ).parent
            /
            "uv"
        )

        if candidate.exists():

            uv_exe = str(
                candidate
            )


    if uv_exe is None:

        raise RuntimeError(
            "Could not locate uv executable."
        )


    print(
        "[38A] uv:",
        uv_exe,
    )


    # ==========================================================================
    # 5. ORIGINAL PYTHON 3.11 CHILD SCRIPT
    # ==========================================================================

    child_script = r'''
import sys
import pandas as pd
import pitindex

start_date = sys.argv[1]
end_date   = sys.argv[2]
csv_path   = sys.argv[3]
info_path  = sys.argv[4]


info = pitindex.info(
    index="sp1500"
)

with open(
    info_path,
    "w",
    encoding="utf-8",
) as f:

    f.write(
        repr(
            info
        )
    )


print(
    "PITINDEX_INFO:"
)

print(
    info
)


hist = pitindex.get_constituents_history(
    start_date,
    end_date,
    index="sp1500",
)


if (
    hist is None
    or
    hist.empty
):

    raise RuntimeError(
        "pitindex returned zero membership rows."
    )


required = {
    "as_of",
    "ticker",
}


missing = (
    required
    -
    set(
        hist.columns
    )
)


if missing:

    raise RuntimeError(
        f"Unexpected pitindex schema. "
        f"Missing={sorted(missing)} "
        f"Available={list(hist.columns)}"
    )


hist[
    "as_of"
] = pd.to_datetime(
    hist[
        "as_of"
    ]
)


final_snapshot = pitindex.get_constituents(
    end_date,
    index="sp1500",
)


if (
    final_snapshot is None
    or
    final_snapshot.empty
):

    raise RuntimeError(
        f"No SP1500 snapshot available at research end {end_date}."
    )


if not (
    1400
    <=
    len(
        final_snapshot
    )
    <=
    1600
):

    raise RuntimeError(
        f"Implausible final SP1500 size: {len(final_snapshot)}"
    )


hist.to_csv(
    csv_path,
    index=False,
)


print()

print(
    "PIT_ROWS=",
    len(
        hist
    )
)

print(
    "PIT_SNAPSHOTS=",
    hist[
        "as_of"
    ].nunique()
)

print(
    "PIT_UNIQUE_TICKERS=",
    hist[
        "ticker"
    ].nunique()
)

print(
    "FINAL_SNAPSHOT_SIZE=",
    len(
        final_snapshot
    )
)
'''


    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".py",
        delete=False,
        encoding="utf-8",
    ) as f:

        f.write(
            child_script
        )

        child_path = (
            f.name
        )


    # ==========================================================================
    # 6. ORIGINAL ISOLATED PITINDEX ENVIRONMENT
    # ==========================================================================

    pitindex_source = (
        "pitindex @ "
        "git+https://github.com/arielNacamulli/pitindex.git"
    )


    cmd = [
        uv_exe,
        "run",

        "--python",
        "3.11",

        "--with",
        pitindex_source,

        "--with",
        "pandas",

        "python",
        child_path,

        B38_PIT_START_DATE.strftime(
            "%Y-%m-%d"
        ),

        V4_DATA_END_DATE.strftime(
            "%Y-%m-%d"
        ),

        str(
            B38_PIT_BRIDGE_CSV
        ),

        str(
            B38_PIT_INFO_TXT
        ),
    ]


    print(
        "\n[38A] Starting isolated Python 3.11..."
    )

    print(
        "[38A] Source: latest pitindex GitHub main"
    )


    try:

        result = subprocess.run(
            cmd,
            check=True,
            text=True,
            capture_output=True,
        )


    except subprocess.CalledProcessError as exc:

        print(
            "\n========== CHILD STDOUT =========="
        )

        print(
            exc.stdout
        )


        print(
            "\n========== CHILD STDERR =========="
        )

        print(
            exc.stderr
        )


        raise RuntimeError(
            "BLOCK 38A bridge failed. "
            "Do not continue to Module 15."
        ) from exc


    finally:

        try:

            os.remove(
                child_path
            )

        except Exception:

            pass


    print(
        "\n========== CHILD OUTPUT =========="
    )

    print(
        result.stdout
    )


# ==============================================================================
# 7. LOAD PIT HISTORY INTO CURRENT NOTEBOOK
# ==============================================================================

if not B38_PIT_BRIDGE_CSV.exists():

    raise RuntimeError(
        "Historical PIT bridge CSV is missing."
    )


B38_PIT_RAW = pd.read_csv(
    B38_PIT_BRIDGE_CSV
)


required = {
    "as_of",
    "ticker",
}


missing = (
    required
    -
    set(
        B38_PIT_RAW.columns
    )
)


if missing:

    raise RuntimeError(
        f"Bridge CSV missing columns: {sorted(missing)}"
    )


B38_PIT_RAW[
    "as_of"
] = pd.to_datetime(
    B38_PIT_RAW[
        "as_of"
    ]
)


# ==============================================================================
# 8. HARD HISTORICAL DATE GATES
# ==============================================================================

if (
    V4_COMPARISON_START
    !=
    pd.Timestamp(
        "2023-10-10"
    )
):

    raise RuntimeError(
        "Historical V4 comparison start changed."
    )


if (
    V4_DATA_END_DATE
    !=
    pd.Timestamp(
        "2026-07-27"
    )
):

    raise RuntimeError(
        "Historical V4 research end changed."
    )


if (
    B38_PIT_START_DATE
    !=
    pd.Timestamp(
        "2021-03-31"
    )
):

    raise RuntimeError(
        "Historical Block-38A PIT start changed."
    )


# ==============================================================================
# 9. ORIGINAL HARD SANITY CHECKS
# ==============================================================================

snapshot_counts = (
    B38_PIT_RAW
    .groupby(
        "as_of"
    )[
        "ticker"
    ]
    .nunique()
)


median_snapshot = float(
    snapshot_counts.median()
)


min_snapshot = int(
    snapshot_counts.min()
)


max_snapshot = int(
    snapshot_counts.max()
)


if not (
    1400
    <=
    median_snapshot
    <=
    1600
):

    raise RuntimeError(
        "SP1500 PIT sanity gate failed: "
        f"median={median_snapshot:.0f}"
    )


if (
    B38_PIT_RAW[
        "as_of"
    ].min()
    >
    B38_PIT_START_DATE
):

    raise RuntimeError(
        "PIT history begins later than requested."
    )


if (
    B38_PIT_RAW[
        "as_of"
    ].max()
    >
    V4_DATA_END_DATE
):

    raise RuntimeError(
        "PIT cache extends beyond the frozen research end."
    )


# ==============================================================================
# 10. OUTPUT
# ==============================================================================

print(
    "\n"
    +
    "=" * 100
)

print(
    "[+] MODULE 14 / BLOCK 38A PASSED"
)

print(
    "=" * 100
)


print(
    f"PIT rows             : "
    f"{len(B38_PIT_RAW):,}"
)

print(
    f"Event snapshots      : "
    f"{snapshot_counts.size:,}"
)

print(
    f"Historical tickers   : "
    f"{B38_PIT_RAW['ticker'].nunique():,}"
)

print(
    f"Median snapshot size : "
    f"{median_snapshot:,.0f}"
)

print(
    f"Snapshot range       : "
    f"{min_snapshot:,} – {max_snapshot:,}"
)

print(
    f"First PIT date       : "
    f"{B38_PIT_RAW['as_of'].min().date()}"
)

print(
    f"Last PIT event       : "
    f"{B38_PIT_RAW['as_of'].max().date()}"
)

print(
    f"Historical cache     : "
    f"{B38A_REUSED_HISTORICAL_CACHE}"
)

print(
    "\nV4 comparison start  :",
    V4_COMPARISON_START.date(),
)

print(
    "V4 research end      :",
    V4_DATA_END_DATE.date(),
)

print(
    "\nV4 master fingerprint:"
)

print(
    V4_MASTER_FINGERPRINT
)

print(
    "\n[+] PIT universe infrastructure is ready."
)

print(
    "[+] NEXT: MODULE 15 — EXACT HISTORICAL BLOCK 38B."
)
