"""
job.py — парсинг lenta.ru и отправка новостей на backend.

Парсер НЕ геокодирует сам — это делает CreateArticleHandler на бэкенде.
Парсер передаёт position (топоним от placeFinder) в поле location.address,
бэкенд сам вызывает Nominatim и получает координаты.
"""

import logging
import os
import re
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup
from natasha import Doc, NewsEmbedding, NewsNERTagger, Segmenter

import placeFinder as pf

logger = logging.getLogger(__name__)

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")
MODEL_PATH  = os.getenv("MODEL_PATH", "models/good_news_finder.pkl")
INGEST_URL  = f"{BACKEND_URL}/articles/"

HEADERS = {
    "Accept": "text/html",
    "User-Agent": (
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:148.0) "
        "Gecko/20100101 Firefox/148.0"
    ),
}

_MONTHS = {
    "января": 1,"февраля": 2,"марта": 3,"апреля": 4,"мая": 5,"июня": 6,
    "июля": 7,"августа": 8,"сентября": 9,"октября": 10,"ноября": 11,"декабря": 12,
}

_DATE_RE = re.compile(
    r"(\d{1,2}):(\d{2}),\s*(\d{1,2})\s+([а-яА-Я]+)\s+(\d{4})"
)

def _parse_date(date_str: str) -> str:
    m = _DATE_RE.search(date_str.strip())

    if m:
        hour, minute, day, month_name, year = m.groups()

        month = _MONTHS.get(month_name.lower())

        if month:
            try:
                dt = datetime(
                    int(year),
                    month,
                    int(day),
                    int(hour),
                    int(minute),
                    tzinfo=timezone.utc,
                )
                return dt.isoformat()

            except ValueError:
                pass

    logger.warning(
        "Не удалось разобрать дату '%s', используем now()",
        date_str
    )

    return datetime.now(timezone.utc).isoformat()


def _send(payload: dict) -> str:
    try:
        resp = requests.post(INGEST_URL, json=payload, timeout=15)
        if resp.status_code in (200, 201):
            return "created"
        if resp.status_code == 409:
            logger.debug("Дубль: %s", payload.get("url"))
            return "duplicate"
        logger.warning("Backend %s для %s: %s",
                       resp.status_code, payload.get("url"), resp.text[:300])
        return "error"
    except requests.RequestException as exc:
        logger.error("Ошибка отправки: %s", exc)
        return "error"


def run_parse_and_send():
    logger.info("=== Старт парсинга ===")

    segmenter  = Segmenter()
    ner_tagger = NewsNERTagger(NewsEmbedding())

    model = pf.init_news_finder()
    model.load_model(MODEL_PATH)

    stats = {"created": 0, "duplicate": 0, "error": 0}

    for page in range(1, 8):
        page_url = f"https://lenta.ru/rubrics/russia/regions/{page}/"
        logger.info("Страница %d → %s", page, page_url)

        try:
            req = requests.get(page_url, headers=HEADERS, timeout=120)
            req.raise_for_status()
        except requests.RequestException as exc:
            logger.error("Ошибка : Страница %d недоступна: %s", page, exc)
            break

        soup      = BeautifulSoup(req.text, "lxml")
        container = soup.find(class_="rubric-page__container _subrubric")
        if not container:
            logger.warning("Нет контейнера на стр.%d", page)
            continue

        items = container.find_all(class_="rubric-page__item _news")
        if items:
            items.pop()

        links = ["https://lenta.ru" + n.find("a").get("href") for n in items]

        for link in links:
            try:
                news_req = requests.get(link, headers=HEADERS, timeout=60)
                news_req.raise_for_status()
            except requests.RequestException as exc:
                logger.warning("Недоступна %s: %s", link, exc)
                stats["error"] += 1
                continue

            soup2 = BeautifulSoup(news_req.text, "lxml")
            try:
                title    = soup2.find(class_="topic-body _news").find("span").text.strip()
                subtitle = soup2.find(class_="topic-body__title-yandex").text.strip()
                text     = soup2.find(class_="topic-body__content js-topic-body-content").text.strip()
                date_str = soup2.find(class_="topic-header__item topic-header__time").text.strip()
            except AttributeError:
                logger.warning("Не удалось распарсить структуру: %s", link)
                stats["error"] += 1
                continue

            # ArticleCreateSchema требует subtitle минимум 10 символов,
            # NewsContent требует непустой subtitle — защищаемся здесь
            if not subtitle:
                subtitle = title
            if len(subtitle) < 10:
                subtitle = (subtitle + " " + title)[:500]

            # NER-теги → список строк (бэкенд ожидает List[str])
            doc = Doc(f"{title} {subtitle} {text}")
            doc.segment(segmenter)
            doc.tag_ner(ner_tagger)
            tags = [span.text for span in doc.spans]

            # position от placeFinder — геокодирует бэкенд (CreateArticleHandler)
            try:
                position = model.define_place(title, subtitle, text)["entity_normal"]
            except Exception as exc:
                logger.warning("define_place для %s: %s", link, exc)
                position = ""

            payload = {
                "url":          link,
                "title":        title,
                "subtitle":     subtitle,
                "published_at": _parse_date(date_str),
                "location": {
                    "region":     position,
                    "city":       "",
                    "address":    position,
                    "latitude":   None,
                    "longitude":  None,
                    "confidence": 0.0,
                },
                "tags": tags,
            }

            result = _send(payload)
            stats[result] += 1

    logger.info("=== Завершено: новых=%d дублей=%d ошибок=%d ===",
                stats["created"], stats["duplicate"], stats["error"])