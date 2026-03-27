#!/usr/bin/env bash
set -euo pipefail

OWNER="liminal-loop"
REPO="iptv-epg-trim"
WORKFLOW_FILE="dev-build.yml"
RELEASE_TAG="dev-latest"

SERVICE_NAME="epg-trim"
SERVICE_USER="epgtrim"
SERVICE_GROUP="epgtrim"
INSTALL_DIR="/opt/epg-trim"
BIN_PATH="${INSTALL_DIR}/epg-trim"
WORK_DIR="/var/lib/epg-trim"
LOG_DIR="/var/log/epg-trim"
ENV_FILE="/etc/default/epg-trim"
SERVICE_FILE="/etc/systemd/system/epg-trim.service"

PLAYLIST_URL=""
EPG_URL=""
INTERVAL_SECONDS="7200"
HOST="0.0.0.0"
PORT="8000"

usage() {
  cat <<'EOF'
Install latest epg-trim dev binary as a systemd service.

Required:
  --playlist-url URL
  --epg-url URL

Optional:
  --owner NAME             GitHub owner (default: liminal-loop)
  --repo NAME              GitHub repo (default: iptv-epg-trim)
  --release-tag TAG        GitHub release tag (default: dev-latest)
  --service-name NAME      systemd service name (default: epg-trim)
  --service-user NAME      service user (default: epgtrim)
  --service-group NAME     service group (default: epgtrim)
  --install-dir PATH       install directory (default: /opt/epg-trim)
  --work-dir PATH          data/work directory (default: /var/lib/epg-trim)
  --log-dir PATH           log directory (default: /var/log/epg-trim)
  --interval-seconds N     refresh interval (default: 7200)
  --host HOST              bind host (default: 0.0.0.0)
  --port PORT              bind port (default: 8000)
  --help

Authentication:
  No token is required. Downloads use public GitHub release asset URLs.
EOF
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

as_root() {
  if [[ "${EUID}" -eq 0 ]]; then
    "$@"
  else
    sudo "$@"
  fi
}

detect_target_names() {
  local arch
  arch="$(uname -m)"

  case "${arch}" in
    x86_64|amd64)
      echo "epg-trim-dev-linux-x86_64"
      ;;
    armv7l)
      echo "epg-trim-dev-linux-armv7l"
      ;;
    aarch64|arm64)
      echo "Unsupported architecture: ${arch}" >&2
      echo "No aarch64 dev artifact is currently produced by CI." >&2
      echo "Use armv7l host/OS, or build on your device from source." >&2
      exit 1
      ;;
    *)
      echo "Unsupported architecture: ${arch}" >&2
      exit 1
      ;;
  esac
}

download_release_asset() {
  local asset_name="$1"
  local out_path="$2"
  local url
  url="https://github.com/${OWNER}/${REPO}/releases/download/${RELEASE_TAG}/${asset_name}"

  echo "Trying public release asset: ${url}"
  if curl -fsSL -o "${out_path}" "${url}"; then
    return 0
  fi

  return 1
}

write_env_file() {
  as_root tee "${ENV_FILE}" >/dev/null <<EOF
PLAYLIST_URL=${PLAYLIST_URL}
EPG_URL=${EPG_URL}
INTERVAL_SECONDS=${INTERVAL_SECONDS}
HOST=${HOST}
PORT=${PORT}
EOF
}

write_service_file() {
  as_root tee "${SERVICE_FILE}" >/dev/null <<EOF
[Unit]
Description=EPG Trim Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${SERVICE_USER}
Group=${SERVICE_GROUP}
WorkingDirectory=${WORK_DIR}
EnvironmentFile=${ENV_FILE}
ExecStart=${BIN_PATH} --playlist-url \
  \${PLAYLIST_URL} --epg-url \${EPG_URL} \
  --interval-seconds \${INTERVAL_SECONDS} --work-dir ${WORK_DIR} \
  --host \${HOST} --port \${PORT}
Restart=always
RestartSec=10
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF
}

main() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --playlist-url)
        PLAYLIST_URL="$2"
        shift 2
        ;;
      --epg-url)
        EPG_URL="$2"
        shift 2
        ;;
      --owner)
        OWNER="$2"
        shift 2
        ;;
      --repo)
        REPO="$2"
        shift 2
        ;;
      --release-tag)
        RELEASE_TAG="$2"
        shift 2
        ;;
      --service-name)
        SERVICE_NAME="$2"
        shift 2
        ;;
      --service-user)
        SERVICE_USER="$2"
        shift 2
        ;;
      --service-group)
        SERVICE_GROUP="$2"
        shift 2
        ;;
      --install-dir)
        INSTALL_DIR="$2"
        BIN_PATH="${INSTALL_DIR}/epg-trim"
        shift 2
        ;;
      --work-dir)
        WORK_DIR="$2"
        shift 2
        ;;
      --log-dir)
        LOG_DIR="$2"
        shift 2
        ;;
      --interval-seconds)
        INTERVAL_SECONDS="$2"
        shift 2
        ;;
      --host)
        HOST="$2"
        shift 2
        ;;
      --port)
        PORT="$2"
        shift 2
        ;;
      --help|-h)
        usage
        exit 0
        ;;
      *)
        echo "Unknown argument: $1" >&2
        usage
        exit 1
        ;;
    esac
  done

  if [[ -z "${PLAYLIST_URL}" || -z "${EPG_URL}" ]]; then
    echo "Both --playlist-url and --epg-url are required." >&2
    usage
    exit 1
  fi

  require_cmd curl
  require_cmd systemctl

  local release_asset_name tmp_dir zip_path executable
  release_asset_name="$(detect_target_names)"
  tmp_dir="$(mktemp -d)"
  zip_path="${tmp_dir}/artifact.zip"

  if download_release_asset "${release_asset_name}" "${zip_path}"; then
    echo "Downloaded release asset: ${release_asset_name}"
    executable="${zip_path}"
  else
    echo "Public release asset is not available: ${release_asset_name}" >&2
    echo "Expected URL: https://github.com/${OWNER}/${REPO}/releases/download/${RELEASE_TAG}/${release_asset_name}" >&2
    echo "Wait for the dev release workflow to publish assets, then retry." >&2
    exit 1
  fi

  echo "Installing executable from: ${executable}"

  if ! getent group "${SERVICE_GROUP}" >/dev/null 2>&1; then
    as_root groupadd --system "${SERVICE_GROUP}"
  fi

  if ! id -u "${SERVICE_USER}" >/dev/null 2>&1; then
    as_root useradd --system --no-create-home --shell /usr/sbin/nologin --gid "${SERVICE_GROUP}" "${SERVICE_USER}"
  fi

  as_root mkdir -p "${INSTALL_DIR}" "${WORK_DIR}" "${LOG_DIR}"
  as_root cp "${executable}" "${BIN_PATH}"
  as_root chmod 0755 "${BIN_PATH}"
  as_root chown root:root "${BIN_PATH}"
  as_root chown -R "${SERVICE_USER}:${SERVICE_GROUP}" "${WORK_DIR}" "${LOG_DIR}"

  ENV_FILE="/etc/default/${SERVICE_NAME}"
  SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

  write_env_file
  write_service_file

  as_root systemctl daemon-reload
  as_root systemctl enable --now "${SERVICE_NAME}"

  echo "Installed and started service: ${SERVICE_NAME}"
  echo "Check status with: sudo systemctl status ${SERVICE_NAME}"
  echo "Follow logs with: journalctl -u ${SERVICE_NAME} -f"

  rm -rf "${tmp_dir}"
}

main "$@"
