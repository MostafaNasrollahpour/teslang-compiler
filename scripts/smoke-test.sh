#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

cleanup() {
    rm -f output.tsl
}

trap cleanup EXIT

echo "Checking Python modules..."
python3 -m py_compile compiler/*.py

echo "Compiling sample program..."
python3 compiler/main.py < examples/sample.teslang

echo "Comparing generated IR..."
diff -u examples/sample.tsl output.tsl

if [[ -x tsvm/tsvm ]]; then
    echo "Executing generated IR with TSVM..."

    actual_output="$(./tsvm/tsvm output.tsl)"
    expected_output="436"

    if [[ "$actual_output" != "$expected_output" ]]; then
        echo "Smoke test failed."
        echo "Expected output: $expected_output"
        echo "Actual output:   $actual_output"
        exit 1
    fi
else
    echo "TSVM executable not found; runtime execution check skipped."
fi

echo "Smoke test passed."
