import pandas as pd
import re
import newspaper
import textacy as tcy
from collections import defaultdict

sites = ["https://www.breitbart.com", "https://www.foxnews.com"]

def article_extractor(newspaper_url, title_topic=None):
    dd = defaultdict(list)

    source = newspaper.build(newspaper_url, memoize_articles=False)
    arts = [i.url for i in source.articles]
    print(source)
    print(len(arts))
    if title_topic is None:
        relevant_arts = [i for i in arts]
    else:
        relevant_arts = [i for i in arts if title_topic in i]

    for i in relevant_arts:
        art = newspaper.build_article(i)
        try:
            art.download()
            art.parse()
            #for key in vars(art).keys():
            #    if key == 'config' or key == 'extractor' or key == 'top_node' or key == 'clean_top_node':
            #        continue
            #    dd[key].append(vars(art)[key])
            dd['title'].append(art.title)
            dd['text'].append(art.text)
        except newspaper.article.ArticleException:
            continue
    return pd.DataFrame.from_dict(dd)

def get_articles(*newspaper_url, **kwargs):
    for url in newspaper_url:
        results = []
        articles = article_extractor(url)
        if len(articles) == 0:
            continue
        articles["paper"] = url
        results.append(articles)
        articles = pd.concat(results)
        articles["text"] = articles.text.map(clean_text)
        articles["text"] = preprocess_articles(articles.text)
        articles.to_pickle(url.split('.')[-2])

def clean_text(string):
    string = re.sub(r"SIGN UP FOR OUR NEWSLETTER", "", string)
    string = re.sub(r"Read more here", "", string)
    string = re.sub(r"REUTERS", "", string)
    string = re.sub(r"\?", "'", string)
    string = re.sub(r"\n", "", string)
    return string

def preprocess_articles(articles):
    clean_arts = []
    for art in articles:
        clean_art = tcy.preprocess.preprocess_text(art,
                                          fix_unicode=True,
                                          lowercase=True,
                                          no_currency_symbols=True,
                                          no_numbers=True,
                                          no_urls=True)
        clean_arts.append(clean_art)
    return clean_arts


get_articles(*sites)

