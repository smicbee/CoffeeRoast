#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

SOLUTION_PATH="${REPO_ROOT}/iRoastControl Software/iRoastControl.sln"
PROJECT_DIR="${REPO_ROOT}/iRoastControl Software"
RELEASE_DIR="${PROJECT_DIR}/bin/Release"
DEST_DIR="${DEST_DIR:-${HOME}/coffeeroastbuild}"
CONFIGURATION="${CONFIGURATION:-Release}"
PLATFORM="${PLATFORM:-Any CPU}"

die() {
  echo "ERROR: $*" >&2
  exit 1
}

copy_release_output() {
  [ -n "${DEST_DIR}" ] || die "Destination directory is empty"
  [ "${DEST_DIR}" != "/" ] || die "Refusing to deploy to /"

  mkdir -p "${DEST_DIR}"

  if command -v rsync >/dev/null 2>&1; then
    rsync -a --delete "${RELEASE_DIR}/" "${DEST_DIR}/"
  else
    find "${DEST_DIR}" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
    cp -a "${RELEASE_DIR}/." "${DEST_DIR}/"
  fi
}

build_solution() {
  local build_command=()

  if command -v nuget >/dev/null 2>&1; then
    nuget restore "${SOLUTION_PATH}"
  elif [ ! -d "${REPO_ROOT}/packages" ]; then
    echo "WARNING: NuGet packages are missing and 'nuget' is not installed; build may fail during reference resolution." >&2
  fi

  if command -v msbuild >/dev/null 2>&1; then
    build_command=(msbuild "${SOLUTION_PATH}" /restore /p:Configuration="${CONFIGURATION}" /p:Platform="${PLATFORM}")
  elif command -v xbuild >/dev/null 2>&1; then
    build_command=(xbuild "${SOLUTION_PATH}" /p:Configuration="${CONFIGURATION}" /p:Platform="${PLATFORM}")
  else
    die "No supported build tool found. Install Visual Studio Build Tools/MSBuild or Mono xbuild."
  fi

  "${build_command[@]}"
}

main() {
  [ -f "${SOLUTION_PATH}" ] || die "Solution file not found: ${SOLUTION_PATH}"

  echo "Building ${SOLUTION_PATH}"
  build_solution

  [ -d "${RELEASE_DIR}" ] || die "Release output folder not found: ${RELEASE_DIR}"
  find "${RELEASE_DIR}" -maxdepth 1 -type f -name '*.exe' | grep -q . || die "No .exe found in ${RELEASE_DIR}"

  echo "Copying release output to ${DEST_DIR}"
  copy_release_output

  echo "Deployment output:"
  find "${DEST_DIR}" -maxdepth 1 -type f -print | sort
}

main "$@"
