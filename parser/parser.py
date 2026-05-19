import requests
import json
from bs4 import BeautifulSoup
#from pymorphy3 import MorphAnalyzer
import placeFinder as pf
from natasha import (
    Segmenter,
    
    NewsEmbedding,
    NewsNERTagger,
    
    PER,
    Doc
)

def parse_lenta():
    segmenter = Segmenter()

    emb = NewsEmbedding()
    ner_tagger = NewsNERTagger(emb)


    st_accept = "text/html" 
    st_useragent = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:148.0) Gecko/20100101 Firefox/148.0"
    headers = {
    "Accept": st_accept,
    "User-Agent": st_useragent
    }

    with open("json_data/News.json","r",encoding="utf-8") as f:
        data = json.load(f)
        for item in data:
            first_item = item
            break

    model = pf.init_news_finder()
    model.load_model("models/good_news_finder.pkl")

    with open('json_data/News.json', 'w', encoding='utf-8') as file:
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
                if title == first_item["title"]:
                    for item in data:
                        json.dump(item,file, indent=4, ensure_ascii=False)
                        if data[-1] != item : file.write(",\n")
                    file.write("]")
                    return 1
                subTitle = news_soup.find(class_="topic-body__title-yandex").text
                mainText = news_soup.find(class_="topic-body__content js-topic-body-content").text
                doc = Doc(title + " " + subTitle + " " + mainText)

                #morph = MorphAnalyzer()

                doc.segment(segmenter)
                doc.tag_ner(ner_tagger)

                #normalise = lambda text: morph.parse(text)[0].normal_form
                title = news_soup.find(class_="topic-body _news").find('span').text
                subTitle = news_soup.find(class_="topic-body__title-yandex").text
                text = news_soup.find(class_="topic-body__content js-topic-body-content").text

                tags = ""
                for i in doc.spans:
                    tags += i.text + ", "
                tags = tags[:-2]
                news = {
                    "title" : title,
                    "subTitle" : subTitle,
                    "date" : news_soup.find(class_="topic-header__item topic-header__time").text,
                    "link" : link,
                    "position" : model.define_place(title,subTitle,text)["entity_normal"],
                    "tags" : tags
                }
                json.dump(news,file, indent=4, ensure_ascii=False)
                if link != links[-1] or page != 7:
                    file.write(",\n")
        file.write("]")

if __name__ == "__main__":
    parse_lenta()