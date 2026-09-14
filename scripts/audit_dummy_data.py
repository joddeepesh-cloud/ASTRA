#!/usr/bin/env python3
"""
ASTRA Automated Dummy/Mock Data Audit Script.
Scans frontend and backend codebases for forbidden mock strings, fake observation IDs,
fake telemetry metrics, and unverified demo flags.
"""

import os
import sys
import re

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_SRC = os.path.join(ROOT_DIR, "frontend", "src")
BACKEND_APP = os.path.join(ROOT_DIR, "backend", "app")

FORBIDDEN_PATTERNS = [
    (re.compile(r"mockData", re.IGNORECASE), "Import or reference to mockData.ts"),
    (re.compile(r"MOCK_OBSERVATIONS"), "Reference to MOCK_OBSERVATIONS"),
    (re.compile(r"MOCK_TELEMETRY"), "Reference to MOCK_TELEMETRY"),
    (re.compile(r"MOCK_HISTORY_RECORDS"), "Reference to MOCK_HISTORY_RECORDS"),
    (re.compile(r"MOCK_COPILOT"), "Reference to MOCK_COPILOT"),
    (re.compile(r"OBS-004271"), "Fake Observation ID OBS-004271"),
    (re.compile(r"OBS-009401"), "Fake Observation ID OBS-009401"),
    (re.compile(r"OBS-001092"), "Fake Observation ID OBS-001092"),
    (re.compile(r"SIMULATED DEMO TELEMETRY"), "Simulated demo telemetry text"),
    (re.compile(r"DEMO HISTORY"), "Demo history text"),
    (re.compile(r"DEMO TRIAGE DATASET"), "Demo triage dataset text"),
    (re.compile(r"12481|11930"), "Fake telemetry counts (12481 / 11930)"),
]

# File extensions to scan
SCANNED_EXTENSIONS = ('.ts', '.tsx', '.js', '.jsx', '.json', '.py')

def audit_directory(dir_path: str) -> list:
    violations = []
    for root, _, files in os.walk(dir_path):
        for file in files:
            if not file.endswith(SCANNED_EXTENSIONS):
                continue
            
            # Skip genuine data artifacts like observationLibrary.json
            if file == "observationLibrary.json" or file.endswith(".png") or file.endswith(".jpg"):
                continue

            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, ROOT_DIR)

            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    for idx, line in enumerate(lines, start=1):
                        for pattern, desc in FORBIDDEN_PATTERNS:
                            if pattern.search(line):
                                violations.append((rel_path, idx, desc, line.strip()))
            except Exception as e:
                violations.append((rel_path, 0, f"Failed to read file: {e}", ""))

    return violations

def main():
    print("=" * 70)
    print("RUNNING ASTRA AUTOMATED DUMMY DATA AUDIT")
    print("=" * 70)

    frontend_violations = audit_directory(FRONTEND_SRC)
    backend_violations = audit_directory(BACKEND_APP)

    all_violations = frontend_violations + backend_violations

    if not all_violations:
        print("✓ SUCCESS: No forbidden mock/demo data references found!")
        print("=" * 70)
        sys.exit(0)
    else:
        print(f"❌ AUDIT FAILED: Found {len(all_violations)} mock/demo data violations:\n")
        for rel_path, line_no, desc, snippet in all_violations:
            print(f"  • [{rel_path}:{line_no}] {desc}")
            print(f"    Code: '{snippet}'\n")
        print("=" * 70)
        sys.exit(1)

if __name__ == "__main__":
    main()
