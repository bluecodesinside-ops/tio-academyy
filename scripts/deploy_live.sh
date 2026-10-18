#!/usr/bin/env bash
# Deploy this project to the live site (tioacademy.online).
# Usage:
#   ./scripts/deploy_live.sh
#   ./scripts/deploy_live.sh --dry-run
set -euo pipefail

HOST="${DEPLOY_HOST:-root@72.62.48.168}"
REMOTE="${DEPLOY_PATH:-/var/www/herin}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DRY_RUN=0

if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
fi

RSYNC_FLAGS=(-avz --human-readable)
if [[ "$DRY_RUN" == "1" ]]; then
  RSYNC_FLAGS+=(--dry-run)
fi

echo "Project: $ROOT"
echo "Target:  $HOST:$REMOTE"
if [[ "$DRY_RUN" == "1" ]]; then
  echo "Mode:    dry-run (nothing will change on the server)"
fi
echo

# Never overwrite live secrets, media, or generated files.
rsync "${RSYNC_FLAGS[@]}" \
  --exclude '.git/' \
  --exclude '.env' \
  --exclude '.env.*' \
  --exclude 'settings.py' \
  --exclude 'venv/' \
  --exclude '.venv/' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude '.DS_Store' \
  --exclude 'db.sqlite3' \
  --exclude 'db.sqlite3-journal' \
  --exclude 'media/' \
  --exclude 'staticfiles/' \
  --exclude 'node_modules/' \
  --exclude 'frontend/node_modules/' \
  --exclude '*.mp4' \
  -e 'ssh -o StrictHostKeyChecking=accept-new' \
  "$ROOT/" \
  "$HOST:$REMOTE/"

if [[ "$DRY_RUN" == "1" ]]; then
  echo
  echo "Dry-run finished. Run without --dry-run to deploy for real."
  exit 0
fi

echo
echo "Running migrate, collectstatic, and restart..."
ssh -o StrictHostKeyChecking=accept-new "$HOST" "bash -s" <<EOF
set -e
cd "$REMOTE"
./venv/bin/python manage.py migrate --noinput
./venv/bin/python manage.py collectstatic --noinput
systemctl restart herin.service
sleep 1
systemctl is-active herin.service
echo "Live deploy done."
EOF
