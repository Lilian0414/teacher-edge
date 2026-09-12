#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID} -ne 0 ]]; then
  echo "Run this installer with sudo." >&2
  exit 1
fi

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPOSITORY_PATH=$(cd -- "${SCRIPT_DIR}/../.." && pwd)
SERVICE_USER=${SUDO_USER:-pi}

if ! id "${SERVICE_USER}" >/dev/null 2>&1; then
  echo "Runtime user does not exist: ${SERVICE_USER}" >&2
  exit 1
fi

SERVICE_GROUP=$(id -gn "${SERVICE_USER}")
case "${REPOSITORY_PATH}" in
  *$'\n'*|*' '*|*'@'*)
    echo "Repository path cannot contain spaces, newlines, or @: ${REPOSITORY_PATH}" >&2
    exit 1
    ;;
esac

python3 -m venv "${REPOSITORY_PATH}/.venv"
"${REPOSITORY_PATH}/.venv/bin/python" -m pip install --upgrade pip
"${REPOSITORY_PATH}/.venv/bin/python" -m pip install -e "${REPOSITORY_PATH}"

install -d -m 0750 -o root -g "${SERVICE_GROUP}" /etc/teacher-edge
if [[ ! -e /etc/teacher-edge/teacher-edge.env ]]; then
  install -m 0600 -o root -g root \
    "${SCRIPT_DIR}/teacher-edge.env.example" \
    /etc/teacher-edge/teacher-edge.env
  echo "Created /etc/teacher-edge/teacher-edge.env; replace its example values before starting the service."
else
  chmod 0600 /etc/teacher-edge/teacher-edge.env
  chown root:root /etc/teacher-edge/teacher-edge.env
  echo "Kept the existing /etc/teacher-edge/teacher-edge.env (values were not displayed)."
fi

sed \
  -e "s|@SERVICE_USER@|${SERVICE_USER}|g" \
  -e "s|@SERVICE_GROUP@|${SERVICE_GROUP}|g" \
  -e "s|@REPOSITORY_PATH@|${REPOSITORY_PATH}|g" \
  "${SCRIPT_DIR}/teacher-edge.service" \
  > /etc/systemd/system/teacher-edge.service
chmod 0644 /etc/systemd/system/teacher-edge.service
systemctl daemon-reload

echo "Installed teacher-edge.service for ${SERVICE_USER}."
echo "After editing the external environment file, run:"
echo "  sudo systemctl enable --now teacher-edge"
