# -*- coding: utf-8 -*-
"""Обновляет AI-дайджест в README профиля.

Источники:
  - Hugging Face API: топ-5 трендовых моделей
  - arXiv API: 5 свежих статей по LLM/NLP (cs.CL)

Скрипт перезаписывает блок README между маркерами DIGEST:START / DIGEST:END.
Зависимости: только стандартная библиотека.
"""
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

README = "README.md"
UA = {"User-Agent": "profile-digest-bot"}


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def hf_trending(n: int = 5) -> list[str]:
    """Топ трендовых моделей Hugging Face."""
    data = json.loads(fetch(
        f"https://huggingface.co/api/models?sort=trendingScore&direction=-1&limit={n}"
    ))
    lines = []
    for m in data[:n]:
        mid = m["id"]
        likes = m.get("likes", 0)
        downloads = m.get("downloads", 0)
        pipeline = m.get("pipeline_tag", "")
        tag = f" `{pipeline}`" if pipeline else ""
        lines.append(
            f"| [{mid}](https://huggingface.co/{mid}){tag} | ❤️ {likes:,} | ⬇️ {downloads:,} |"
        )
    return lines


def arxiv_latest(n: int = 5) -> list[str]:
    """Свежие статьи arXiv по cs.CL (NLP/LLM)."""
    xml_data = fetch(
        "https://export.arxiv.org/api/query?search_query=cat:cs.CL"
        f"&sortBy=submittedDate&sortOrder=descending&max_results={n}"
    )
    ns = {"a": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(xml_data)
    lines = []
    for entry in root.findall("a:entry", ns)[:n]:
        title = re.sub(r"\s+", " ", entry.find("a:title", ns).text).strip()
        link = entry.find("a:id", ns).text.strip()
        date = entry.find("a:published", ns).text[:10]
        if len(title) > 90:
            title = title[:87] + "..."
        lines.append(f"- [{title}]({link}) · `{date}`")
    return lines


def build_section() -> str:
    msk = datetime.now(timezone(timedelta(hours=3)))
    parts = ["\n### 🔥 Trending on Hugging Face\n",
             "| Model | Likes | Downloads |",
             "|---|---|---|"]
    try:
        parts += hf_trending()
    except Exception as e:  # источник недоступен — не валим весь дайджест
        parts.append(f"| _Hugging Face API unavailable: {e}_ | | |")

    parts += ["", "### 📄 Fresh LLM/NLP papers (arXiv cs.CL)", ""]
    try:
        parts += arxiv_latest()
    except Exception as e:
        parts.append(f"- _arXiv API unavailable: {e}_")

    parts.append(
        f"\n<sub>🕐 Auto-updated hourly · last refresh: "
        f"{msk.strftime('%Y-%m-%d %H:%M')} MSK</sub>\n"
    )
    return "\n".join(parts)


def main():
    with open(README, encoding="utf-8") as f:
        text = f.read()

    new = re.sub(
        r"(<!--DIGEST:START-->).*?(<!--DIGEST:END-->)",
        lambda m: m.group(1) + "\n" + build_section() + "\n" + m.group(2),
        text,
        flags=re.S,
    )

    with open(README, "w", encoding="utf-8", newline="\n") as f:
        f.write(new)
    print("README updated")


if __name__ == "__main__":
    main()
