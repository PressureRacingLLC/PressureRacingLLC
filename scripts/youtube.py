"""Write the latest YouTube uploads into README.md between the YOUTUBE markers.

Runs in .github/workflows/youtube.yml. Standard library only.
    python scripts/youtube.py <channel_id> [count]
"""
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from html import escape

NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
START, END = "<!-- YOUTUBE:START -->", "<!-- YOUTUBE:END -->"


def latest(channel, count):
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel}"
    with urllib.request.urlopen(url, timeout=30) as r:
        root = ET.fromstring(r.read())
    out = []
    for e in root.findall("a:entry", NS)[:count]:
        vid = e.find("yt:videoId", NS).text
        out.append((vid, e.find("a:title", NS).text or "", e.find("a:link", NS).get("href")))
    return out


def render(videos):
    cells = []
    for vid, title, link in videos:
        t = escape(title, quote=True)
        cells.append(
            f'<td align="center" width="33%"><a href="{link}">'
            f'<img src="https://i.ytimg.com/vi/{vid}/hqdefault.jpg" width="260" alt="{t}"></a>'
            f"<br><sub><b>{escape(title)}</b></sub></td>")
    return "<table align=\"center\"><tr>\n" + "\n".join(cells) + "\n</tr></table>"


def main():
    channel = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    videos = latest(channel, count)
    if not videos:
        print("feed empty, README left as is")
        return
    readme = open("README.md", encoding="utf-8").read()
    block = f"{START}\n{render(videos)}\n{END}"
    new = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: block, readme, flags=re.S)
    if new != readme:
        open("README.md", "w", encoding="utf-8", newline="\n").write(new)
        print(f"updated with {len(videos)} videos")
    else:
        print("no change")


if __name__ == "__main__":
    main()
