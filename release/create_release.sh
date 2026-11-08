#!/usr/bin/env bash
# 创建 GitHub Release v0.37.0 并上传 wheel + sdist
set -e

cd /f/github/auto_robot
GIT="/c/Program Files/Git/bin/git.exe"
PY=".venv/Scripts/python.exe"
REPO="gsk74521/auto_rf"
TAG="v0.37.0"

TOKEN=$(printf "protocol=https\nhost=github.com\n\n" | "$GIT" credential fill 2>/dev/null | awk -F= '/^password=/{print $2; exit}')
if [ -z "$TOKEN" ]; then
  echo "ERROR: no GitHub token available"
  exit 1
fi

echo "=== 1) create tag ==="
"$GIT" tag -a "$TAG" -m "auto_rf $TAG" 2>/dev/null || echo "tag already exists"
"$GIT" push origin "$TAG" 2>&1 | tail -3

echo "=== 2) create release ==="
"$PY" - <<'PYEOF'
import json
body = open('release/RELEASE_NOTES_v0.37.0.md', encoding='utf-8').read()
with open('release/.release_body.json', 'w', encoding='utf-8') as f:
    json.dump({
        "tag_name": "v0.37.0",
        "name": "auto_rf v0.37.0 — rf-mcp 增强版",
        "body": body,
        "draft": False,
        "prerelease": False,
    }, f, ensure_ascii=False)
print("body json written")
PYEOF

RESP=$(curl -s -X POST "https://api.github.com/repos/$REPO/releases" \
  -H "Authorization: token $TOKEN" \
  -H "Accept: application/vnd.github+json" \
  --data-binary @release/.release_body.json)

RELEASE_ID=$(echo "$RESP" | "$PY" -c "import sys,json; print(json.load(sys.stdin).get('id',''))")
if [ -z "$RELEASE_ID" ]; then
  echo "ERROR creating release:"; echo "$RESP" | head -30; exit 1
fi
echo "release id: $RELEASE_ID"

echo "=== 3) upload assets ==="
for f in release/rf_mcp_enhanced-0.37.0-py3-none-any.whl release/rf_mcp_enhanced-0.37.0.tar.gz; do
  name=$(basename "$f")
  code=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
    "https://uploads.github.com/repos/$REPO/releases/$RELEASE_ID/assets?name=$name" \
    -H "Authorization: token $TOKEN" \
    -H "Content-Type: application/octet-stream" \
    --data-binary @"$f")
  echo "upload $name -> HTTP $code"
done

rm -f release/.release_body.json
echo "DONE: https://github.com/$REPO/releases/tag/$TAG"
