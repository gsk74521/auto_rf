"""验证 GitHub Release v0.37.0 的真实状态。"""
import json
import time
import urllib.request

URL = "https://api.github.com/repos/gsk74521/auto_rf/releases/tags/v0.37.0"

for attempt in range(5):
    try:
        req = urllib.request.Request(URL)
        req.add_header("Accept", "application/vnd.github+json")
        with urllib.request.urlopen(req, timeout=60) as r:
            d = json.load(r)
        break
    except Exception as e:
        print(f"attempt {attempt+1}: {e}")
        time.sleep(2 * (attempt + 1))
else:
    raise SystemExit("failed to fetch release")

print("tag       :", d["tag_name"])
print("name      :", d["name"])
print("draft     :", d["draft"], "| prerelease:", d["prerelease"])
print("url       :", d["html_url"])
print("body_len  :", len(d.get("body") or ""))
print("assets    :", len(d.get("assets", [])))
for a in d.get("assets", []):
    print(f"  - {a['name']}  {a['size']} bytes")
    print(f"    {a['browser_download_url']}")
