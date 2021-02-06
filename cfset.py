# -*- coding: utf-8 -*-
"""
Created on Thu Aug 27 20:59:09 2020

@author: JenNeng
"""
import nltk
import multiprocessing
import string
import pandas as pd
import numpy as np
from functools import partial
from nltk import WordNetLemmatizer

class ConfusionSet():
    def __init__(self):
        self.vocabularies = self.get_vocabularies()
        self.MAX_DL_DISTANCE = 1 #Get suggestion list with dl distance of one cost only
    
    def get_dl_distance(self, s1, s2,transposition=True):
        if (abs((len(s1)-len(s2)))>self.MAX_DL_DISTANCE+1): 
            return None  #fail fast to retrieve cost possible 1 distance only
        
        matrix_map = [[i + j for j in range(len(s2) + 1)]
                      for i in range(len(s1) + 1)]
    
        for i in range(len(s1)):
            for j in range(len(s2)):
                char1, char2 = s1[i], s2[j]
                cost = 0 if (char1 == char2) else 1
    
                matrix_map[i + 1][j + 1] = min([
                    matrix_map[i][j + 1] + 1,  #deletion
                    matrix_map[i + 1][j] + 1,  #insertion
                    matrix_map[i][j] + cost  #substitution or no change
                ])
    
                if transposition and i >= 1 and j >= 1 and s1[i] == s2[j-1] and s1[i-1] == s2[j]:
                    matrix_map[i + 1][j + 1] = min(
                        [matrix_map[i + 1][j + 1], matrix_map[i - 1][j - 1] + cost])
                    
        return matrix_map[-1][-1]
    
    def process_input(self, input_string):
        splitted_string = self.remove_punctuation(input_string)
        return splitted_string, self.get_lemmatization(splitted_string)
    
    def remove_punctuation(self, input_string):
        return np.asarray(input_string.translate(str.maketrans('','',string.punctuation)).split())
    
    def get_lemmatization(self, input_string_array):
        lemma_func = np.vectorize(lambda x: WordNetLemmatizer().lemmatize(x))
        return lemma_func(input_string_array)
    
    def get_vocabularies(self):
        return pd.read_csv("corpus/vocabularies.csv").to_numpy()[:,0].astype(str)
    
    def get_suggestion(self, vocabulary, word):
        if(self.get_dl_distance(word.lower(),vocabulary.lower()) == self.MAX_DL_DISTANCE):
            return vocabulary
        return

    def is_nonword_error(self, input_string):
        # Check non-word error
        is_nonword_error = False
        lemma_str = WordNetLemmatizer().lemmatize(input_string).lower()
        if lemma_str not in self.vocabularies and input_string not in string.punctuation:
            is_nonword_error = True
        return is_nonword_error

    def get_suggestion_list(self, input_string):
        suggestion_dict = {}
        input_string_array, lemma_string_array = self.process_input(input_string)
        pool = multiprocessing.Pool(4)

        for index, word in enumerate(lemma_string_array):
            suggestion = pool.map(partial(self.get_suggestion,word=word), self.vocabularies)
            suggestion = [suggest for suggest in suggestion if suggest is not None]
            suggestion.insert(0, word)
            input_word = input_string_array[index]
            suggestion_dict[input_word]=suggestion
        return suggestion_dict
