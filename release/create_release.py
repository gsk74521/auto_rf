"""创建 GitHub Release v0.37.1 并上传 wheel + sdist（带重试）。"""
import json
import subprocess
import time
import urllib.error
import urllib.request

REPO = "gsk74521/auto_rf"
TAG = "v0.37.1"
GIT = r"C:\Program Files\Git\bin\git.exe"


def get_token() -> str:
    out = subprocess.run(
        [GIT, "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True, text=True,
    )
    for line in out.stdout.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    raise SystemExit("no GitHub token available")


def api(method, url, token, data=None, content_type="application/json", retries=6):
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, method=method)
            req.add_header("Authorization", f"token {token}")
            req.add_header("Accept", "application/vnd.github+json")
            if data is not None:
                req.add_header("Content-Type", content_type)
                req.data = data
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "ignore")
            last = f"HTTP {e.code}: {body[:300]}"
            print(f"  attempt {attempt+1} failed: {last}")
            if e.code in (401, 403, 404):
                raise
            time.sleep(2 * (attempt + 1))
        except Exception as e:
            last = str(e)
            print(f"  attempt {attempt+1} failed: {last}")
            time.sleep(2 * (attempt + 1))
    raise SystemExit(f"API failed after retries: {last}")


def main():
    token = get_token()

    releases = api("GET", f"https://api.github.com/repos/{REPO}/releases?per_page=100", token)
    existing = next((r for r in releases if r.get("tag_name") == TAG), None)
    if existing:
        rel = existing
        print(f"release exists: id={rel['id']} {rel['html_url']}")
    else:
        body = open("release/RELEASE_NOTES_v0.37.1.md", encoding="utf-8").read()
        payload = json.dumps({
            "tag_name": TAG,
            "name": "auto_rf v0.37.1 — rf-mcp 增强版",
            "body": body,
            "draft": False,
            "prerelease": False,
        }).encode("utf-8")
        rel = api("POST", f"https://api.github.com/repos/{REPO}/releases", token, payload)
        print(f"created release: id={rel['id']} {rel['html_url']}")

    rid = rel["id"]
    have = {a["name"] for a in rel.get("assets", [])}
    for path in [
        "release/rf_mcp_enhanced-0.37.1-py3-none-any.whl",
        "release/rf_mcp_enhanced-0.37.1.tar.gz",
        "release/SHA256SUMS-v0.37.1.txt",
    ]:
        name = path.rsplit("/", 1)[-1]
        if name in have:
            print(f"asset exists, skip: {name}")
            continue
        with open(path, "rb") as f:
            data = f.read()
        asset = api(
            "POST",
            f"https://uploads.github.com/repos/{REPO}/releases/{rid}/assets?name={name}",
            token, data, content_type="application/octet-stream",
        )
        print(f"uploaded {name}: {asset.get('browser_download_url')}")

    print("DONE:", rel["html_url"])


if __name__ == "__main__":
    main()
