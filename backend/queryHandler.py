from natasha import (
    Segmenter,
    NewsEmbedding,
    NewsMorphTagger,
    NewsSyntaxParser,
    NewsNERTagger,
    Doc
)

from pymorphy3 import *

class QueryParser:
    def __init__(self):
        self.segmenter = Segmenter()
        self.emb = NewsEmbedding()
        self.morph_tagger = NewsMorphTagger(self.emb)
        self.syntax_parser = NewsSyntaxParser(self.emb)
        self.ner_tagger = NewsNERTagger(self.emb)
        self.morph = MorphAnalyzer()
    
    def normalise(self, text: str) -> str:
        return text
        p = self.morph.parse(text)[0]
        return p.normal_form
    
    def parse(self, query: str):
        doc = Doc(query)
        doc.segment(self.segmenter)
        doc.tag_morph(self.morph_tagger)
        doc.parse_syntax(self.syntax_parser)
        doc.tag_ner(self.ner_tagger)

        result = {
            'tags': set(),
            'geo': set()
        }

        for span in doc.spans:
            if span.type == 'LOC':
                result['geo'].add(self.normalise(span.text).lower())
                result['tags'].add(self.normalise(span.text).lower())
        
        for token in doc.tokens:
            if token.pos in ['ADP', 'CCONJ', 'PART', 'INTJ', 'PUNCT', 'ADJ']:
                continue
            result['tags'].add(self.normalise(token.text).lower())
        print(result)
        return result