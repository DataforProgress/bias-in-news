from os import listdir
from os.path import isfile, isdir, join
from dateutil import parser
from collections import OrderedDict
import csv
import re
import pymysql.cursors


def split_articles(text):
    # Sometimes there's a random header, hard to deal with, remove anything above first doc
    pattern = re.compile(r' 1 of [0-9]+ DOCUMENTS', re.MULTILINE)
    text = pattern.split(text)[-1]
    pattern = re.compile(r'[0-9]+ of [0-9]+ DOCUMENTS', re.MULTILINE)
    articles = pattern.split(text)
    return articles


def get_date(article_lines):
    # there will be a date, find it
    d = None
    for i, line in enumerate(article_lines):
        try:
            d = parser.parse(line, fuzzy=True)
        except ValueError:
            continue
        break
    return OrderedDict([('DATE:', {'idx': i, 'val': d})])


def get_field_idx_val(i_init, article_lines, fields):
    field_dict = OrderedDict([(field, {'idx': len(article_lines), 'val': None}) for field in fields])
    for idx, line in enumerate(article_lines[i_init:]):
        check = [field for field in fields if field in line]
        if len(check) == 1:
            field_dict[check[0]]['idx'] = i_init + idx
            field_dict[check[0]]['val'] = line.split(check[0])[-1]
            removed = fields[0]
            while check[0] not in removed:
                removed = fields[0]
                fields.remove(removed)
        if len(fields) == 0:
            break
    return field_dict


def parse_pre_meta(i_date, article_lines):
    fields = ['BYLINE:', 'SECTION:', 'LENGTH:', 'HIGHLIGHT:']
    field_dict = get_field_idx_val(i_date, article_lines, fields.copy())
    # The headline should be two lines above the first line in pre_meta
    i_headline = min(field_dict.values(), key=lambda field: field['idx'] - 2)['idx']
    headline = article_lines[i_headline]
    i_pre_meta = max(field_dict.values(), key=lambda field: field['idx'] if field['idx'] != len(article_lines) else -1)['idx']
    field_dict.update({'HEADLINE:': {'idx': i_headline, 'val': headline}})
    return i_pre_meta, field_dict


def parse_post_meta(i_pre_meta, article_lines):
    fields = ['URL:', 'GRAPHIC:', 'LANGUAGE:', 'DOCUMENT-TYPE:', 'PUBLICATION-TYPE:', 'SUBJECT:', 'PERSON:', 'CITY:', 'STATE:', 'COUNTRY:']
    field_dict = get_field_idx_val(i_pre_meta, article_lines, fields.copy())
    i_text = i_pre_meta + 2
    text = article_lines[i_text:min(field_dict.values(), key=lambda field: field['idx'] - 2)['idx']]
    text = ' '.join([line if line != '' else '\n' for line in text])
    field_dict.update({'TEXT:': {'idx': i_text, 'val': text}})
    return field_dict


def get_article_field_dict(article):
    article_lines = article.splitlines()
    field_dict = get_date(article_lines)
    if field_dict['DATE:']['idx'] == len(article_lines) - 1:
        return None
    i_pre_meta, pre_meta_dict = parse_pre_meta(field_dict['DATE:']['idx'], article_lines)
    post_meta_dict = parse_post_meta(i_pre_meta, article_lines)
    pre_meta_dict.update(post_meta_dict)
    field_dict.update(pre_meta_dict)
    return field_dict

# Connect to the database


def insert_articles(field_dicts):
    with connection.cursor() as cursor:
        # Create a new record
        for field_dict in field_dicts:
            field_dict['DATE:']['val'] = field_dict['DATE:']['val'].strftime('%Y-%m-%d %H:%M:%S')
            field_dict['LENGTH:']['val'] = ''.join(filter(str.isdigit, field_dict['LENGTH:']['val']))
            keys = '`, `'.join(['A_' +k[:-1].replace('-','_') for k in field_dict.keys()])
            vals = [str(v['val']) for v in field_dict.values()]
            sql = "INSERT INTO `articles` (`" + keys + "`) VALUES (" + "%s, " * (len(vals) - 1) + " %s)"
            cursor.execute(sql, vals)
    connection.commit()



def get_source_field_dicts(source, text):
    articles = split_articles(text)
    field_dicts = []
    for article in articles:
        field_dict = OrderedDict([('SOURCE:', {'idx': -1, 'val': source})])
        article_field_dict = get_article_field_dict(article)
        if article_field_dict is not None:
            field_dict.update(article_field_dict)
            field_dicts.append(field_dict)
    return field_dicts


def read_sources(write_csv=False, write_mysql=False):
    sources = [d for d in listdir('sources/') if isdir('sources/' + d)]
    print(sources)
    for source in sources:
        print(source)
        source_path = 'sources/' + source + '/'
        files = [f for f in listdir(source_path) if isfile(join(source_path, f))]
        write_header = True
        for f_path in files:
            with open(source_path + f_path, "r", encoding="utf8") as f:
                field_dicts = get_source_field_dicts(source, f.read())
            print(f_path + " LEN: " + str(len(field_dicts)))

            if write_mysql:
                insert_articles(field_dicts)

            if write_csv:
                field_dict = {k: [field_dict[k]['val'] for field_dict in field_dicts] for k in field_dicts[0].keys()}
                if write_header:
                    with open(source + ".csv", "w") as outfile:
                        writer = csv.writer(outfile)
                        writer.writerow(list(field_dict.keys()))
                    write_header = False

                with open(source + ".csv", "a") as outfile:
                    writer = csv.writer(outfile)
                    writer.writerows(zip(*field_dict.values()))

connection = pymysql.connect(host='localhost',
                             user='root',
                             password='',
                             db='bias_in_news',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)

read_sources(write_mysql=True)

connection.close()


























