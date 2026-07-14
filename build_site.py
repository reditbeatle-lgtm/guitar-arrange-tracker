#!/usr/bin/env python3
"""Generate the Guitar Arrange Tracker HTML from YouTube search results."""
import json
import html
import os
import re
import sys

SCRATCH = sys.argv[1]
TODAY = sys.argv[2]  # YYYY-MM-DD
ROOT = os.path.dirname(os.path.abspath(__file__))

KW_CLASSICAL = "classical guitar arrangement"
KW_ACOUSTIC = "acoustic guitar cover"

CSS = """
:root{--bg:#faf8f5;--card:#ffffff;--accent:#b5713f;--text:#3a3128;--muted:#8a7d6e;}
*{box-sizing:border-box;}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Hiragino Kaku Gothic ProN","Yu Gothic",Meiryo,sans-serif;
background:var(--bg);color:var(--text);line-height:1.6;}
.wrap{max-width:1100px;margin:0 auto;padding:20px 16px 60px;}
.backlink{display:inline-block;color:var(--accent);text-decoration:none;font-size:.95rem;margin-bottom:12px;}
.backlink:hover{text-decoration:underline;}
h1{font-size:1.8rem;margin:.2em 0;color:var(--accent);}
.meta{color:var(--muted);font-size:.9rem;margin-bottom:24px;}
.section-head{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin:34px 0 14px;
border-bottom:2px solid #e7ddd0;padding-bottom:8px;}
.section-head h2{font-size:1.3rem;margin:0;color:var(--text);}
.playall{background:var(--accent);color:#fff;text-decoration:none;font-size:.85rem;
padding:6px 14px;border-radius:20px;white-space:nowrap;transition:background .15s;}
.playall:hover{background:#9a5d31;}
.count-badge{color:var(--muted);font-size:.85rem;}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:16px;}
.card{background:var(--card);border-radius:12px;overflow:hidden;text-decoration:none;color:inherit;
box-shadow:0 1px 4px rgba(80,60,40,.08);transition:transform .18s ease,box-shadow .18s ease;
display:flex;flex-direction:column;}
.card:hover{transform:translateY(-5px);box-shadow:0 8px 20px rgba(120,80,40,.18);}
.thumb{width:100%;aspect-ratio:16/9;object-fit:cover;background:#eee;display:block;}
.card-body{padding:12px 14px 16px;display:flex;flex-direction:column;gap:4px;}
.card-title{font-weight:600;font-size:.98rem;line-height:1.35;
display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;}
.card-channel{color:var(--accent);font-size:.85rem;}
.card-date{color:var(--muted);font-size:.78rem;}
.empty{background:var(--card);border-radius:12px;padding:28px;text-align:center;color:var(--muted);}
.archive-list{list-style:none;padding:0;}
.archive-list li{background:var(--card);border-radius:10px;margin-bottom:10px;
box-shadow:0 1px 4px rgba(80,60,40,.08);}
.archive-list a{display:block;padding:14px 18px;text-decoration:none;color:var(--accent);font-weight:600;}
.archive-list a:hover{background:#f3ece2;}
""".strip()


def esc(s):
    return html.escape(s or "", quote=True)


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def extract(data, keyword):
    out = []
    for it in data.get("items", []):
        vid = it.get("id", {}).get("videoId")
        if not vid:
            continue
        sn = it.get("snippet", {})
        out.append({
            "videoId": vid,
            # YouTube returns HTML-encoded entities in title/channel; unescape to raw first,
            # then we re-escape safely at render time.
            "title": html.unescape(sn.get("title", "")),
            "channel": html.unescape(sn.get("channelTitle", "")),
            "published": sn.get("publishedAt", ""),
            "url": "https://www.youtube.com/watch?v=" + vid,
            "keyword": keyword,
        })
    return out


def fmt_date(iso):
    # 2026-07-14T11:00:32Z -> 2026-07-14
    return iso.split("T")[0] if iso else ""


def card_html(v):
    thumb = f"https://i.ytimg.com/vi/{esc(v['videoId'])}/mqdefault.jpg"
    return f"""      <a class="card" href="{esc(v['url'])}" target="_blank" rel="noopener">
        <img class="thumb" src="{thumb}" alt="{esc(v['title'])}" loading="lazy">
        <div class="card-body">
          <div class="card-title">{esc(v['title'])}</div>
          <div class="card-channel">{esc(v['channel'])}</div>
          <div class="card-date">{esc(fmt_date(v['published']))}</div>
        </div>
      </a>"""


def section_html(heading, videos):
    ids = ",".join(v["videoId"] for v in videos)
    playall = ""
    if videos:
        play_url = "https://www.youtube.com/watch_videos?video_ids=" + esc(ids)
        playall = f'<a class="playall" href="{play_url}" target="_blank" rel="noopener">▶ 全部まとめて再生</a>'
    head = f"""    <div class="section-head">
      <h2>{esc(heading)}</h2>
      <span class="count-badge">{len(videos)} 件</span>
      {playall}
    </div>"""
    if not videos:
        body = '    <div class="empty">このカテゴリの新着動画は見つかりませんでした。</div>'
    else:
        cards = "\n".join(card_html(v) for v in videos)
        body = f'    <div class="grid">\n{cards}\n    </div>'
    return head + "\n" + body


def build_page(today, classical, acoustic, total):
    page = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ギターアレンジ・トラッカー {esc(today)}</title>
<style>
{CSS}
</style>
</head>
<body>
<div class="wrap">
  <a class="backlink" href="archive.html">← アーカイブ一覧へ</a>
  <h1>ギターアレンジ・トラッカー</h1>
  <div class="meta">検索日: {esc(today)} ／ 総件数: {total} 件</div>
"""
    if total == 0:
        page += '  <div class="empty">本日（過去24時間）は新着動画が見つかりませんでした。</div>\n'
    else:
        page += section_html("クラシックギター・アレンジ", classical) + "\n"
        page += section_html("アコースティックギター・カバー", acoustic) + "\n"
    page += """</div>
</body>
</html>
"""
    return page


def build_archive_index():
    files = []
    adir = os.path.join(ROOT, "archive")
    if os.path.isdir(adir):
        for fn in os.listdir(adir):
            m = re.fullmatch(r"(\d{4}-\d{2}-\d{2})\.html", fn)
            if m:
                files.append(m.group(1))
    files = sorted(set(files), reverse=True)
    items = "\n".join(
        f'    <li><a href="archive/{d}.html">{d}</a></li>' for d in files
    ) or '    <li class="empty" style="list-style:none;">アーカイブはまだありません。</li>'
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ギターアレンジ・トラッカー アーカイブ</title>
<style>
{CSS}
</style>
</head>
<body>
<div class="wrap">
  <a class="backlink" href="index.html">← 最新版へ</a>
  <h1>ギターアレンジ・トラッカー アーカイブ</h1>
  <div class="meta">過去の検索結果一覧（{len(files)} 日分）</div>
  <ul class="archive-list">
{items}
  </ul>
</div>
</body>
</html>
"""


def main():
    s1 = extract(load(os.path.join(SCRATCH, "s1.json")), KW_CLASSICAL)
    s2 = extract(load(os.path.join(SCRATCH, "s2.json")), KW_ACOUSTIC)

    seen = set()
    classical, acoustic = [], []
    for v in s1 + s2:
        if v["videoId"] in seen:
            continue
        seen.add(v["videoId"])
        if v["keyword"] == KW_CLASSICAL:
            classical.append(v)
        else:
            acoustic.append(v)
    total = len(classical) + len(acoustic)

    page = build_page(TODAY, classical, acoustic, total)
    with open(os.path.join(ROOT, "archive", f"{TODAY}.html"), "w", encoding="utf-8") as f:
        f.write(page)
    with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)
    with open(os.path.join(ROOT, "archive.html"), "w", encoding="utf-8") as f:
        f.write(build_archive_index())

    print(f"classical={len(classical)} acoustic={len(acoustic)} total={total}")


if __name__ == "__main__":
    main()
