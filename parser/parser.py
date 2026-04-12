import requests
import json
from bs4 import BeautifulSoup
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


st_accept = "text/html" 
st_useragent = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:148.0) Gecko/20100101 Firefox/148.0"
headers = {
   "Accept": st_accept,
   "User-Agent": st_useragent
}


with open('News.json', 'w', encoding='utf-8') as file:
    file.write("[\n")
    for page in range(1,8):
        print(f"page {page} ")
        req = requests.get(f"https://lenta.ru/rubrics/russia/regions/{page}/", headers)
        print(f"https://lenta.ru/rubrics/russia/regions/{page}/")
        src = req.text
        soup = BeautifulSoup(src, 'lxml')
        news = soup.find(class_="rubric-page__container _subrubric").find_all(class_="rubric-page__item _news")
        news.pop()
        links = []
        for n in news:
            links.append("https://lenta.ru" + n.find('a').get('href'))  
        for link in links:
            print(f"link {link}\n")
            #if link == "https://lenta.ru/news/2026/04/11/virusolog-raskryl-mesto-obitaniya-v-rossii-opasnyh-komarov/":
            #    break
            news_req = requests.get(link, headers)
            news_src = news_req.text
            news_soup = BeautifulSoup(news_src, 'lxml')
            title = news_soup.find(class_="topic-body _news").find('span').text
            subTitle = news_soup.find(class_="topic-body__title-yandex").text
            mainText = news_soup.find(class_="topic-body__content js-topic-body-content").text
            doc = Doc(title + subTitle + mainText)


            doc.segment(segmenter)
            doc.tag_ner(ner_tagger)
            flag = 1
            for i in doc.spans:
                if i.type == 'LOC':
                    position = i.text
                    flag = 0
                    break
            if flag:
                continue
            tags = ""
            for i in doc.spans:
                tags += i.text + ", "
            news = {
                "title" : news_soup.find(class_="topic-body _news").find('span').text,
                "subTitle" : news_soup.find(class_="topic-body__title-yandex").text,
                "date" : news_soup.find(class_="topic-header__item topic-header__time").text,
                "link" : link,
                "position" : position,
                "tags" : tags
            }
            json.dump(news,file, indent=4, ensure_ascii=False)
            if link != links[-1] & page == 7:
                file.write(",\n")
    file.write("]")