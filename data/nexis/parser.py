from os import listdir
from os.path import isfile, join
import csv

def split(pub,text):
    if pub == 'NYT':
        articles = text.split('              Copyright')
    elif pub == 'WashPo':
        articles = text.split('                        All Rights Reserved')
    return articles

def clean_article_text(section, word):
    spl = section[1].split(word)
    section[1] = spl[0]
    section.insert(2, word + spl[1])
    return section

def get_article_sections(article):
    #breaks the articles up into 3 sections. Metadata section 1, including title, byline and section, article text, and metadata section 2, including subject and url
    #There is no clear marker to delineate these, so it has to be done by finding multile consectutive blank lines, which denotes a section break
    break_count = 0
    section_num = 0
    break_log = []
    sections = ['', '', '', '', '', '', '', '', '', '']
    for line in article.splitlines():
        if len(line) == 0:
            break_log.append(break_count)
            break_count+=1
        elif section_num == 3 and line.split(' ')[0] == 'LANGUAGE':
            break_count = 0
            section_num += 1
        elif len(line) > 0 and break_count >= 2 and section_num != 3:
            section_num += 1
            sections[section_num] = line
            break_count=0
            break_log.append(break_count)
        elif len(line) > 0:
            break_count = 0
            sections[section_num] = sections[section_num] + ' ' + line
    #removes 2 junk sections
    sections = sections[2:]
    #the highlight metadata gets put into its own section when it shouldnt this places it in the metadata1 section
    if ('HIGHLIGHT:') in sections[1]:
        sections[0] += sections[1]
        sections.pop(1)
    #sometimes the metadata2 is not seperated from the article text by the double line breaks. This checks in the article text for meta keywords and breakd them out
    for meta_string in ['URL:','LANGUAGE:']:
        if (meta_string) in sections[1]:
            clean_article_text(sections,meta_string)
    return sections


def clean_meta1(meta):
    cleaned = {}
    if ("BYLINE:") in meta:
        meta = meta.split("BYLINE:")
        cleaned['title'] = meta[0]
        meta = meta[1]
        meta = meta.split("SECTION:")
        cleaned['byline'] = meta[0]
    else:
        cleaned['byline'] = ''
        cleaned['title'] = meta.split("SECTION:")[0]
        meta = meta.split("SECTION:")
        cleaned['section'] = meta[0]
    meta = meta[1].split("LENGTH:")
    section = meta[0]
    length = meta[1]
    return [cleaned['title'],cleaned['byline'],section,length]


files = [f for f in listdir('WashPo/') if isfile(join('WashPo/', f))]

for f_path in files:
    try:
        f = open("WashPo/" + f_path, "r", encoding="utf8")
        text = f.read()
        f.close()
        print(f_path)

        data = []
        articles = split('WashPo', text)
        for article in articles:
            sects = get_article_sections(article)
            data.append(sects)

        w = csv.writer(open("result20.csv", "a"))

        for row in data:
            w.writerow(row)
    except:
        print("FAILED: " + str(f_path))
