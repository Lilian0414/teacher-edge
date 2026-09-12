#!/usr/bin/env bash
set -euo pipefail

PINNED_TEACHER_SHA=c1b6a03c1894df2d2b8994cf3b9a124ea8b381e5

if [[ ${EUID} -ne 0 ]]; then
  echo "Run this installer with sudo." >&2
  exit 1
fi
if [[ $# -ne 1 ]]; then
  echo "Usage: sudo $0 /absolute/path/to/teacher" >&2
  exit 1
fi

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
TEACHER_REPOSITORY_PATH=$(realpath -- "$1")
SERVICE_USER=${SUDO_USER:-pi}
TEACHER_PYTHON=${TEACHER_PYTHON:-python3}

if ! id "${SERVICE_USER}" >/dev/null 2>&1; then
  echo "Runtime user does not exist: ${SERVICE_USER}" >&2
  exit 1
fi
SERVICE_GROUP=$(id -gn "${SERVICE_USER}")
case "${TEACHER_REPOSITORY_PATH}" in
  *$'\n'*|*' '*|*'@'*|*'|'*|*'&'*|*'\\'*)
    echo "Teacher repository path contains a character unsafe for unit rendering: ${TEACHER_REPOSITORY_PATH}" >&2
    exit 1
    ;;
esac

if [[ ! -f "${TEACHER_REPOSITORY_PATH}/requirements.lock" ]] || \
   [[ ! -f "${TEACHER_REPOSITORY_PATH}/pyproject.toml" ]]; then
  echo "Not a Teacher checkout: ${TEACHER_REPOSITORY_PATH}" >&2
  exit 1
fi
ACTUAL_SHA=$(git -C "${TEACHER_REPOSITORY_PATH}" rev-parse HEAD)
if [[ "${ACTUAL_SHA}" != "${PINNED_TEACHER_SHA}" ]]; then
  echo "Teacher checkout must be pinned to ${PINNED_TEACHER_SHA}; found ${ACTUAL_SHA}." >&2
  exit 1
fi
if [[ "${TEACHER_PYTHON}" =~ [[:space:]] ]]; then
  echo "TEACHER_PYTHON must name a single executable, without arguments." >&2
  exit 1
fi
if ! runuser --user "${SERVICE_USER}" -- "${TEACHER_PYTHON}" -c \
  'import sys; raise SystemExit(sys.version_info < (3, 12))'; then
  echo "Python 3.12 or newer is required (checked: ${TEACHER_PYTHON})." >&2
  echo "Set TEACHER_PYTHON to another interpreter executable if needed." >&2
  exit 1
fi

# All checkout-local artifacts are created by the unprivileged runtime user.
if [[ -e "${TEACHER_REPOSITORY_PATH}/.venv" ]]; then
  chown -R "${SERVICE_USER}:${SERVICE_GROUP}" "${TEACHER_REPOSITORY_PATH}/.venv"
fi
runuser --user "${SERVICE_USER}" -- "${TEACHER_PYTHON}" -m venv \
  "${TEACHER_REPOSITORY_PATH}/.venv"
runuser --user "${SERVICE_USER}" -- \
  "${TEACHER_REPOSITORY_PATH}/.venv/bin/python" -m pip install --upgrade pip
runuser --user "${SERVICE_USER}" -- \
  "${TEACHER_REPOSITORY_PATH}/.venv/bin/python" -m pip install \
  -r "${TEACHER_REPOSITORY_PATH}/requirements.lock"
runuser --user "${SERVICE_USER}" -- \
  "${TEACHER_REPOSITORY_PATH}/.venv/bin/python" -m pip install \
  --no-deps -e "${TEACHER_REPOSITORY_PATH}"

install -d -m 0750 -o "${SERVICE_USER}" -g "${SERVICE_GROUP}" /var/lib/teacher
install -d -m 0750 -o root -g root /etc/teacher
if [[ ! -e /etc/teacher/teacher.env ]]; then
  install -m 0600 -o root -g root "${SCRIPT_DIR}/teacher-core.env.example" \
    /etc/teacher/teacher.env
  echo "Created /etc/teacher/teacher.env; replace GROQ_API_KEY before starting."
else
  chmod 0600 /etc/teacher/teacher.env
  chown root:root /etc/teacher/teacher.env
  echo "Kept existing /etc/teacher/teacher.env (values were not displayed)."
fi

sed -e "s|@SERVICE_USER@|${SERVICE_USER}|g" \
    -e "s|@SERVICE_GROUP@|${SERVICE_GROUP}|g" \
    -e "s|@TEACHER_REPOSITORY_PATH@|${TEACHER_REPOSITORY_PATH}|g" \
    "${SCRIPT_DIR}/teacher-core.service" \
    > /etc/systemd/system/teacher-core.service
chmod 0644 /etc/systemd/system/teacher-core.service
systemctl daemon-reload

echo "Installed teacher-core.service for Teacher ${ACTUAL_SHA}."
echo "Edit /etc/teacher/teacher.env, then run:"
echo "  sudo systemctl enable --now teacher-core"
