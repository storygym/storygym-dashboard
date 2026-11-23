"""Ambil statistik channel YouTube Story Gym lewat YouTube Data API v3.

Menulis:
  site/data.json     -> data terbaru untuk dashboard
  site/history.json  -> riwayat harian (subscriber, total penayangan) untuk grafik

Butuh environment variable YOUTUBE_API_KEY. Hanya membaca data publik.
Tanpa library tambahan (hanya standard library Python).
"""
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

CHANNEL_ID = os.environ.get("CHANNEL_ID", "UCP6KpeMOV2BEUoYcOGRUG8A")
API_KEY = os.environ.get("YOUTUBE_API_KEY", "").strip()
API = "https://www.googleapis.com/youtube/v3/"
SITE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "site")
WITA = timezone(timedelta(hours=8))


def api(endpoint, **params):
    params["key"] = API_KEY
    url = API + endpoint + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        if endpoint == "commentThreads" and e.code == 403:
            return {"items": [], "_error": "comments disabled"}
        sys.exit(f"YouTube API error {e.code} on {endpoint}: {body[:300]}")


def duration_seconds(iso):
    m = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return 0
    d, h, mi, s = (int(x or 0) for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + s


def main():
    if not API_KEY:
        sys.exit("YOUTUBE_API_KEY belum diisi (GitHub > Settings > Secrets and variables > Actions).")

    ch = api("channels", part="snippet,statistics,contentDetails", id=CHANNEL_ID)
    if not ch.get("items"):
        sys.exit(f"Channel {CHANNEL_ID} tidak ditemukan.")
    ch = ch["items"][0]
    stats = ch["statistics"]
    uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]

    # Semua video yang diupload
    ids, token = [], None
    while True:
        p = {"part": "contentDetails", "playlistId": uploads, "maxResults": 50}
        if token:
            p["pageToken"] = token
        res = api("playlistItems", **p)
        ids += [it["contentDetails"]["videoId"] for it in res.get("items", [])]
        token = res.get("nextPageToken")
        if not token:
            break

    videos = []
    for i in range(0, len(ids), 50):
        res = api("videos", part="snippet,statistics,contentDetails", id=",".join(ids[i:i + 50]))
        for v in res.get("items", []):
            st = v.get("statistics", {})
            secs = duration_seconds(v["contentDetails"].get("duration"))
            videos.append({
                "id": v["id"],
                "title": v["snippet"]["title"],
                "published": v["snippet"]["publishedAt"],
                "seconds": secs,
                "short": secs <= 180,
                "views": int(st.get("viewCount", 0)),
                "likes": int(st.get("likeCount", 0)),
                "comments": int(st.get("commentCount", 0)),
                "url": f"https://www.youtube.com/{'shorts/' if secs <= 180 else 'watch?v='}{v['id']}",
            })
    videos.sort(key=lambda x: x["views"], reverse=True)

    # Komentar terbaru (publik). "Belum dibalas" = belum ada balasan sama sekali.
    ct = api("commentThreads", part="snippet", allThreadsRelatedToChannelId=CHANNEL_ID,
             maxResults=50, order="time", textFormat="plainText")
    titles = {v["id"]: v["title"] for v in videos}
    comments = []
    for t in ct.get("items", []):
        s = t["snippet"]
        top = s["topLevelComment"]["snippet"]
        if top.get("authorChannelId", {}).get("value") == CHANNEL_ID:
            continue
        comments.append({
            "video": titles.get(s.get("videoId"), s.get("videoId", "")),
            "author": top.get("authorDisplayName", ""),
            "text": top.get("textDisplay", "")[:300],
            "published": top.get("publishedAt"),
            "replies": int(s.get("totalReplyCount", 0)),
        })

    now = datetime.now(WITA)
    data = {
        "updated": now.strftime("%d %b %Y, %H.%M WITA"),
        "updatedIso": now.isoformat(),
        "channel": {
            "title": ch["snippet"]["title"],
            "subscribers": None if stats.get("hiddenSubscriberCount") else int(stats.get("subscriberCount", 0)),
            "views": int(stats.get("viewCount", 0)),
            "videos": int(stats.get("videoCount", 0)),
        },
        "videos": videos,
        "comments": comments,
    }

    os.makedirs(SITE, exist_ok=True)
    with open(os.path.join(SITE, "data.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    # Riwayat: satu titik per hari (yang terakhir di hari itu menang)
    hist_path = os.path.join(SITE, "history.json")
    try:
        with open(hist_path, encoding="utf-8") as f:
            history = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        history = []
    day = now.strftime("%Y-%m-%d")
    history = [h for h in history if h.get("date") != day]
    history.append({"date": day, "subscribers": data["channel"]["subscribers"],
                    "views": data["channel"]["views"], "videos": data["channel"]["videos"]})
    history.sort(key=lambda h: h["date"])
    with open(hist_path, "w", encoding="utf-8") as f:
        json.dump(history[-365:], f, ensure_ascii=False, indent=1)

    unreplied = sum(1 for c in comments if c["replies"] == 0)
    print(f"OK: {len(videos)} video, {data['channel']['views']} penayangan, "
          f"{data['channel']['subscribers']} subscriber, {unreplied} komentar belum dibalas")


if __name__ == "__main__":
    main()
