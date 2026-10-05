#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only OR LicenseRef-KymoStudio-Commercial
# Copyright (c) 2026 Christof Seidel
# -----------------------------------------------------------------------------
# build-installer.sh - full build: PyInstaller + Inno Setup -> Setup.exe
#
# Requires Inno Setup 6 (autodetected or ISCC_PATH).
#
# Environment:
#   PYTHON, CLEAN, INSTALL_DEPS   passed on to build.sh
#   ISCC_PATH                     path to ISCC.exe (otherwise autodetect)
#   SKIP_PYINSTALLER=1            only run the Inno Setup step
#   APP_VERSION=1.2.3             version (default: python/Core/version.py)
#
#   bash tools/build/build-installer.sh
# -----------------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ISS_FILE="${SCRIPT_DIR}/KymoStudio.iss"
PYTHON="${PYTHON:-python}"

if [[ "${SKIP_PYINSTALLER:-0}" != "1" ]]; then
    bash "${SCRIPT_DIR}/build.sh"
fi

ISCC="${ISCC_PATH:-}"
if [[ -z "${ISCC}" ]]; then
    for candidate in \
        "/c/Program Files (x86)/Inno Setup 6/ISCC.exe" \
        "/c/Program Files/Inno Setup 6/ISCC.exe" \
        "C:/Program Files (x86)/Inno Setup 6/ISCC.exe" \
        "C:/Program Files/Inno Setup 6/ISCC.exe"; do
        if [[ -f "${candidate}" ]]; then ISCC="${candidate}"; break; fi
    done
fi
if [[ -z "${ISCC}" ]] && command -v iscc >/dev/null 2>&1; then ISCC="iscc"; fi
[[ -n "${ISCC}" ]] || { echo "!! ISCC.exe not found. Install Inno Setup 6 or set ISCC_PATH." >&2; exit 1; }

cd "${PROJECT_ROOT}"
APP_VERSION="${APP_VERSION:-$("${PYTHON}" -c "import sys; sys.path.insert(0, 'python'); from Core.version import __version__; print(__version__)")}"
echo ">> Inno Setup: ${ISCC}"
echo ">> Version:    ${APP_VERSION}"

# Git Bash/MSYS would otherwise turn /DAppVersion=... into a path.
MSYS2_ARG_CONV_EXCL="${MSYS2_ARG_CONV_EXCL:-};/DAppVersion=" \
    "${ISCC}" "/DAppVersion=${APP_VERSION}" "${ISS_FILE}"

INSTALLER="${PROJECT_ROOT}/build/installer/KymoStudio_${APP_VERSION}_Setup.exe"
[[ -f "${INSTALLER}" ]] || { echo "!! Installer not found: ${INSTALLER}" >&2; exit 1; }
echo ">> Done: ${INSTALLER}"
