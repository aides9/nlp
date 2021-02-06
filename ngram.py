#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 18 20:56:22 2020
@author: wangwei
"""
import re
import numpy as np
import nltk
import multiprocessing
from functools import partial
from collections import Counter
from nltk.util import ngrams


class NGramProb():
    def __init__(self):
        self.corpus_list = ['t_1.txt', 't_2.txt', 't_3.txt'];
        self.data_collection = []
        for c in self.corpus_list:
            c = 'corpus/' + c
            data = self.read_data(c)
            self.data_collection += data

    def read_data(self, path):
        file = open(path, 'r', encoding='utf-8').read()
        pattern = re.compile(r'<content>(.*?)</content>', re.S)
        contents = pattern.findall(file)
        contents = [i for i in contents if i != '']
        return contents

    def tuple_edit(self, t):
        l = len(t)
        t1 = ()
        last_value = t[l - 1] + '.'
        last_value_list = []
        last_value_list.append(last_value)
        t2 = tuple(last_value_list)
        t1 = t1 + t[0:l - 1] + t2
        return t1

    def ngram_training(self, key, ngram_num):  # Accourding you input n value for ngram and analy inputwords in  the corpus
        total_grams = []
        words = []
        for doc in self.data_collection:
            split_words = list(doc.split(' '))
            # molecular
            [total_grams.append(tuple(split_words[i: i + ngram_num])) for i in range(len(split_words) - ngram_num + 1)]
            # denominator
            [words.append(tuple(split_words[i:i + ngram_num - 1])) for i in range(len(split_words) - ngram_num + 2)]
        total_word_counter = Counter(total_grams)
        word_counter = Counter(words)
        count_molecular = total_word_counter[key]  # if P(B|A) = count(A,B)/count(A) it is the value of count(A,B) key is value like bigram .(A,B)
        count_denominator = word_counter[key[:ngram_num - 1]]  # count(A) value
        count_molecular_change = total_word_counter[
            self.tuple_edit(key)]  # Sample:if (to,want) not in corpus try to check (to ,want.)
        if count_molecular == 0 and count_molecular_change != 0:
            count_molecular = count_molecular_change
        if count_molecular != 0 and count_denominator != 0:
            next_word_prob = count_molecular / count_denominator
        elif count_molecular == 0:
            next_word_prob = 0
        return next_word_prob

    def precision(self, ngramlist, ngram_num):
        ngram_probability = []
        for ngram in ngramlist:
            p = self.ngram_training(ngram, ngram_num)
            ngram_probability.append(p)
        t = self.score_cal(ngram_probability)
        return t * pow(10, 9)

    def score_cal(self, list_prob): # Calculate score of left bigram and right bigram
        result = 0
        for prob in list_prob:
            result += prob
        return result

    def ngram_cal(self, input_string, ngram_num):
        unigrams = nltk.word_tokenize(input_string)
        ngramlist = list(ngrams(unigrams, ngram_num))
        return self.precision(ngramlist, ngram_num)
