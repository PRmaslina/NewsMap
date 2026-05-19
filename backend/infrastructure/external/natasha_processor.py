# infrastructure/external/natasha_processor.py
import re
import os
from typing import List
from natasha import (
    Doc,
    NewsNERTagger,
    NewsEmbedding,
    Segmenter,  # ← добавляем сегментер
)
from pymorphy3 import MorphAnalyzer
from domain.services.query_processor import QueryProcessor, ProcessedQuery


class NatashaQueryProcessor(QueryProcessor):
    def __init__(self) -> None:
        cache_dir = os.getenv("NATASHA_CACHE_DIR", "/app/.natasha_cache")
        os.makedirs(cache_dir, exist_ok=True)
        os.environ["NATASHA_CACHE_DIR"] = cache_dir

        # ✅ Инициализируем все необходимые компоненты
        self.segmenter = Segmenter()
        emb = NewsEmbedding()
        self.ner = NewsNERTagger(emb)
        self.morph = MorphAnalyzer()

        self.ALLOWED_POS = {"NOUN", "VERB", "ADJ", "ADV", "PROPN"}

    async def process(self, text: str) -> ProcessedQuery:
        # 1. Очистка и нормализация
        cleaned = re.sub(r"[^\w\sа-яА-ЯёЁ-]", " ", text).lower()

        # 2. Создаём Doc и применяем пайплайн обработки ✅
        doc = Doc(cleaned)
        doc.segment(self.segmenter)  # ← обязательная сегментация
        doc.tag_ner(self.ner)  # ← правильный способ применения NER

        lemmas = []
        geo_candidates = []

        # 3. Итерируем по токенам с тегами
        for token in doc.tokens:  # type: ignore
            # 🚫 Фильтруем служебные части речи
            if token.pos not in self.ALLOWED_POS:
                continue

            if any(
                token.start >= s.start and token.stop <= s.stop
                for s in doc.spans  # type: ignore
                if s.type == "LOC"
            ):
                geo_candidates.append(token.text.lower())

            # 🔤 Лемматизация через pymorphy3
            parsed = self.morph.parse(token.text)[0]
            lemma = parsed.normal_form
            if len(lemma) > 1:
                lemmas.append(lemma)

        # 4. Сборка tsquery-совместимой строки
        ts_query = " & ".join(lemmas) if lemmas else ""

        if not ts_query and cleaned.strip():
            # Если Natasha всё утащила в географию, берём очищенные слова как есть
            ts_query = " & ".join(word for word in cleaned.split() if word)

        return ProcessedQuery(
            query=ts_query, keywords=lemmas, geo_terms=list(set(geo_candidates))
        )

