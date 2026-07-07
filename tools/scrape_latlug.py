#!/usr/bin/env python3
# LatLUG migration scraper
# Crawls latlug.lv (Drupal 7) and exports forum topics, news articles
# and the user list to JSON files for migration to the new site.
#
# Usage:
#   pip install requests beautifulsoup4
#   python3 scrape_latlug.py
#
# Output: data/forum.json, data/news.json, data/users.json
# Takes ~3-5 minutes (polite 0.4s delay between requests).

import json
import os
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE = "http://latlug.lv"
NL = chr(10)
DELAY = 0.4
HEADERS = {"User-Agent": "LatLUG-migration-scraper/1.0 (site owner migration)"}

FORUM_CATEGORIES = {
    "biedriba": "Biedrība",
    "pasakumi": "Pasākumi",
    "atbalsts": "Atbalsts",
    "attistiba": "Attīstība",
    "moci-un-modeli": "MOCi un Modeļi",
    "konkursi": "Konkursi",
}

session = requests.Session()
session.headers.update(HEADERS)


def get_soup(url):
    time.sleep(DELAY)
    r = session.get(url, timeout=30)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def text_of(el):
    if el is None:
        return ""
    return el.get_text(separator=NL, strip=True)


def parse_submitted(el):
    """'Pievienoja Lauris Kļaviņš Se, 04.07.2020 18:46' -> (author, date)."""
    if el is None:
        return ("", "")
    author_link = el.find("a")
    author = text_of(author_link)
    raw = text_of(el).replace("Pievienoja", "").replace("Pastāvīga saite", "")
    date = raw.replace(author, "").strip().strip(",").strip()
    return (author, date)


def collect_pages(first_url):
    """Yield soups for first_url and all pager-next pages."""
    url = first_url
    while url:
        soup = get_soup(url)
        yield soup
        nxt = soup.select_one("li.pager-next a")
        url = urljoin(BASE, nxt.get("href")) if nxt else None


def author_slug(el):
    if el is None:
        return ""
    link = el.find("a")
    if link and link.get("href", "").startswith("/users/"):
        return link["href"].replace("/users/", "")
    return ""


def scrape_forum():
    topics = []
    users = {}
    for slug, name in FORUM_CATEGORIES.items():
        print("Category:", name)
        topic_urls = []
        for soup in collect_pages(BASE + "/forumi/" + slug):
            for a in soup.select("td a"):
                href = a.get("href", "")
                if href.startswith("/forum/") and href not in topic_urls:
                    topic_urls.append(href)
        print("  topics found:", len(topic_urls))
        for href in topic_urls:
            url = urljoin(BASE, href)
            try:
                soup = get_soup(url)
            except Exception as e:
                print("  FAILED", url, e)
                continue
            h1 = soup.select_one("h1")
            node = soup.select_one(".node-forum")
            sub = soup.select_one(".node-forum .submitted") or soup.select_one(".submitted")
            author, date = parse_submitted(sub)
            aslug = author_slug(sub)
            if author:
                u = users.setdefault(aslug or author, {"name": author, "slug": aslug, "posts": 0})
                u["posts"] += 1
            body = soup.select_one(".node-forum .field-name-body")
            comments = []
            for c in soup.select(".comment"):
                csub = c.select_one(".submitted")
                cauthor, cdate = parse_submitted(csub)
                caslug = author_slug(csub)
                if cauthor:
                    u = users.setdefault(caslug or cauthor, {"name": cauthor, "slug": caslug, "posts": 0})
                    u["posts"] += 1
                cbody = c.select_one(".field-name-comment-body") or c.select_one(".content")
                comments.append({
                    "author": cauthor,
                    "author_slug": caslug,
                    "date": cdate,
                    "body_text": text_of(cbody),
                    "body_html": str(cbody) if cbody else "",
                })
            topics.append({
                "url": url,
                "category_slug": slug,
                "category": name,
                "title": text_of(h1),
                "author": author,
                "author_slug": aslug,
                "date": date,
                "body_text": text_of(body),
                "body_html": str(body) if body else "",
                "comments": comments,
            })
            print("  ok:", text_of(h1)[:50], "(", len(comments), "comments )")
    return topics, users


def scrape_news(users):
    articles = []
    seen = set()
    for soup in collect_pages(BASE + "/"):
        for h2a in soup.select("h2 a"):
            href = h2a.get("href", "")
            if not href.startswith("/") or href.startswith("/forum"):
                continue
            if href in seen:
                continue
            seen.add(href)
            url = urljoin(BASE, href)
            try:
                s = get_soup(url)
            except Exception as e:
                print("FAILED", url, e)
                continue
            h1 = s.select_one("h1")
            sub = s.select_one(".submitted")
            author, date = parse_submitted(sub)
            aslug = author_slug(sub)
            if author:
                u = users.setdefault(aslug or author, {"name": author, "slug": aslug, "posts": 0})
                u["posts"] += 1
            body = s.select_one(".field-name-body")
            images = []
            if body:
                for img in body.select("img"):
                    src = img.get("src", "")
                    if src:
                        images.append(urljoin(BASE, src))
            articles.append({
                "url": url,
                "path": href,
                "title": text_of(h1),
                "author": author,
                "author_slug": aslug,
                "date": date,
                "body_text": text_of(body),
                "body_html": str(body) if body else "",
                "images": images,
            })
            print("news ok:", text_of(h1)[:50])
    return articles


def main():
    os.makedirs("data", exist_ok=True)
    topics, users = scrape_forum()
    articles = scrape_news(users)
    with open("data/forum.json", "w", encoding="utf-8") as f:
        json.dump(topics, f, ensure_ascii=False, indent=1)
    with open("data/news.json", "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=1)
    user_list = sorted(users.values(), key=lambda u: -u["posts"])
    with open("data/users.json", "w", encoding="utf-8") as f:
        json.dump(user_list, f, ensure_ascii=False, indent=1)
    print(NL + "DONE")
    print("topics:", len(topics))
    print("articles:", len(articles))
    print("users:", len(user_list))


if __name__ == "__main__":
    main()
