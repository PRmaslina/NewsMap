

from natasha import (
    Segmenter,
    
    NewsEmbedding,
    NewsNERTagger,
    
    PER,
    Doc
)

segmenter = Segmenter()

emb = NewsEmbedding()
ner_tagger = NewsNERTagger(emb)

text = '''
В Белгородской области из-за атак беспилотных летательных аппаратов (БПЛА) 
Вооруженных сил Украины (ВСУ) пострадали две женщины. 
Об этом сообщил глава российского региона Вячеслав Гладков в своем Telegram-канале.
Губернатор уточнил, что в Шебекино в результате детонации дрона 16-летняя девушка получила баротравму. 
Ее госпитализировали. «В городе Грайворон при сбитии FPV-дрона пострадала женщина. 
С ранением колена бригада скорой доставила ее в Грайворонскую ЦРБ», 
— написал губернатор Белгородской области.
'''
doc = Doc(text)


doc.segment(segmenter)
doc.tag_ner(ner_tagger)
for i in doc.spans:
    print(i)
    print("\n")

