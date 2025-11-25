#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(pwd)"
BRANCH="all-changes-$(date -u +%Y%m%dT%H%M%SZ)"
REMOTE="origin"
BACKUP_DIR="backups"
BACKUP_FILE="${BACKUP_DIR}/cam_full_backup_$(date -u +%Y%m%dT%H%M%SZ).tgz"

# ensure backup dir exists
mkdir -p "${BACKUP_DIR}"

echo "Creating backup archive: ${BACKUP_FILE}"
tar czf "${BACKUP_FILE}" --exclude='.git' .

echo "Creating branch: ${BRANCH}"
git fetch "${REMOTE}" || true
git checkout -b "${BRANCH}"

echo "Staging all files (this includes untracked files)"
git add -A

# if nothing to commit, exit
if git diff --cached --quiet; then
  echo "Nothing to commit (no staged changes). Exiting."
  exit 0
fi

COMMIT_MSG="snapshot: commit all changes $(date -u +%Y-%m-%dT%H:%M:%SZ)"
git commit -m "${COMMIT_MSG}"

NEW_COMMIT=$(git rev-parse --short HEAD)
echo "Committed ${NEW_COMMIT}: ${COMMIT_MSG}"

# add a short git note with context (if notes are enabled)
NOTE="Full snapshot commit created on $(date -u +%Y-%m-%dT%H:%M:%SZ)
Backup: ${BACKUP_FILE}
Branch: ${BRANCH}
Commit: ${NEW_COMMIT}"
echo "${NOTE}" | git notes add -F - || echo "git notes add failed or notes not enabled; continuing"

echo "Pushing branch ${BRANCH} to ${REMOTE}"
git push -u "${REMOTE}" "${BRANCH}"

echo "Done. Recent commits:"
git --no-pager log --oneline --decorate -n 10
