#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
# Copyright (c) 2026 Christof Seidel
# -----------------------------------------------------------------------------
# build.sh - builds the KymoStudio executable with PyInstaller (onedir).
#
# Output:
#   build/work/              PyInstaller intermediate files
#   build/dist/KymoStudio/   bundled application
#
# Environment:
#   PYTHON          Python interpreter (default: python)
#   CLEAN=1         delete build/work, build/dist and build/installer first
#   INSTALL_DEPS=1  pip install -r requirements-build.txt first
#
#   bash tools/build/build.sh
#   CLEAN=1 INSTALL_DEPS=1 bash tools/build/build.sh
# -----------------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
SPEC_FILE="${SCRIPT_DIR}/KymoStudio.spec"
BUILD_DIR="${PROJECT_ROOT}/build"
PYTHON="${PYTHON:-python}"

cd "${PROJECT_ROOT}"
echo ">> Project root: ${PROJECT_ROOT}"
echo ">> Python:       $(${PYTHON} --version 2>&1)"

if [[ "${CLEAN:-0}" == "1" ]]; then
    echo ">> Removing build/work, build/dist, build/installer ..."
    rm -rf "${BUILD_DIR}/work" "${BUILD_DIR}/dist" "${BUILD_DIR}/installer"
fi

if [[ "${INSTALL_DEPS:-0}" == "1" ]]; then
    "${PYTHON}" -m pip install --upgrade pip
    "${PYTHON}" -m pip install -r requirements-build.txt
fi

"${PYTHON}" -m PyInstaller "${SPEC_FILE}" --noconfirm \
    --distpath "${BUILD_DIR}/dist" --workpath "${BUILD_DIR}/work"

EXE_NAME="KymoStudio"
if [[ "$(uname -s)" =~ MINGW|MSYS|CYGWIN ]] || [[ "${OS:-}" == "Windows_NT" ]]; then
    EXE_NAME="KymoStudio.exe"
fi
ARTIFACT="${BUILD_DIR}/dist/KymoStudio/${EXE_NAME}"
[[ -e "${ARTIFACT}" ]] || { echo "!! Artefact not found: ${ARTIFACT}" >&2; exit 1; }
echo ">> Done: ${ARTIFACT}"
