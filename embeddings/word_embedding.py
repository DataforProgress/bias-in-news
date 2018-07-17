#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

import os.path

import logging
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

import csv
csv.field_size_limit(sys.maxsize)

import gensim
from gensim.summarization.textcleaner import split_sentences, tokenize_by_word
from gensim.models import Phrases

# whether to retrain models
force_retrain = False

# whether to run tests
test_acc = False

# currently available: nyt, washpo
source_name = 'nyt'
source_path = 'source_embeddings/' + source_name

data_source = 'nexis'

if not os.path.isfile(source_path) or force_retrain:
    with open('../data/%s.csv' % source_name) as f:
        reader = csv.reader(f)
        articles = [r[1] for r in reader]
    sentences = []
    for article in articles:
        art = split_sentences(article)
        sentences += [list(tokenize_by_word(sen)) for sen in art]
    bigram_transformer = Phrases(sentences)
    sentences = bigram_transformer[sentences]
    model = gensim.models.Word2Vec(sentences, size=100, window=10, min_count=2, workers=10)
    model.train(sentences, total_examples=len(sentences), epochs=50)
    model.save(source_path)
else:
    model = gensim.models.Word2Vec.load(source_path)

if test_acc:
    model.accuracy('questions-words.txt')


def get_similarity_of_pairs(pairs):
    """
    Takes list of tuples of word pairs and prints the similarity of those pairs
    :param pairs: tuples of word pairs to print similarity of
    :return:
    """
    for w1, w2 in pairs:
        print('(' + w1 + ', ' + w2 + ') = ' + str(model.wv.similarity('clinton', 'health')))


def get_most_similar(words):
    """
    Given a list of strings prints the top most similar words
    :param words: list of strings in dictionary of model
    :return:
    """
    for w in words:
        print('Similar to ' + w + ': ' + str(model.wv.most_similar(positive=w)))


def get_analogy(pos, neg):
    """
    given lists of lists of positive and negative words prints top most similar words
    :param pos: list of lists of positive words, overall len same as neg
    :param neg: list of lists of negative words, overall len same as pos
    :return:
    """
    assert len(pos) == len(neg), "Different number of equations incompatible, append empty lists for only pos/neg"
    for i in range(len(pos)):
        print(' + '.join(pos[i]) + ' - ' + ' - '.join(neg[i]) + ' = ' +
              str(model.most_similar_cosmul(positive=pos[i], negative=neg[i], topn=10)))

# Examples
pairs = [('clinton', 'leader'), ('trump', 'leader'), ('obama', 'leader')]
get_similarity_of_pairs(pairs)

words = ['immigrant', 'queer', 'proud', 'leftist']
get_most_similar(words)

pos = [['immigrant', 'white'], ['immigrant', 'latino']]
neg = [['black'], ['white']]
get_analogy(pos, neg)
