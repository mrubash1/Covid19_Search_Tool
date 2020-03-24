import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer 
import re
import os
from pathlib import Path
from rank_bm25 import BM25Okapi
import numpy as np


'''
To prepare the text for the search index we perform the following steps
1.   Remove punctuations and special characters
2.   Convert to lowercase
3.   Tokenize into individual tokens (words mostly)
4.   Remove stopwords like (and, to))
5.   Lemmatize
'''

def strip_characters(text):
    t = re.sub('\(|\)|:|,|;|\.|’|”|“|\?|%|>|<', '', text)
    t = re.sub('/', ' ', t)
    t = t.replace("'",'')
    return t

def clean(text):
    t = text.lower()
    t = strip_characters(t)
    return t

def tokenize(text):
    words = nltk.word_tokenize(text)
    english_stopwords = list(set(stopwords.words('english')))
    return list(set([word for word in words 
                     if len(word) > 1
                     and not word in english_stopwords
                     and not (word.isnumeric() and len(word) != 4)
                     and (not word.isnumeric() or word.isalpha())] )
               )
    
def lemmatize(word_list,lemmatizer):
    # Init the Wordnet Lemmatizer
    lemmatized_output = ' '.join([lemmatizer.lemmatize(w) for w in word_list])
    return lemmatized_output

def preprocess(text):
    t = clean(text)
    tokens = tokenize(t)
    lemmatizer=WordNetLemmatizer()
    tokens = lemmatize(tokens,lemmatizer)
    return tokens


class SearchResults:
    
    def __init__(self, 
                 data: pd.DataFrame,
                 columns = None):
        self.results = data
        if columns:
            self.results = self.results[columns]
            
    def __getitem__(self, item):
        return Paper(self.results.loc[item])
    
    def __len__(self):
        return len(self.results)
        
    def _repr_html_(self):
        return self.results._repr_html_()

class WordTokenIndex:
    
    def __init__(self, 
                 corpus: pd.DataFrame, 
                 columns):
        self.corpus = corpus
        raw_search_str = self.corpus.abstract.fillna('') + ' ' + self.corpus.title.fillna('')
        self.index = raw_search_str.apply(preprocess).to_frame()
        self.index.columns = ['terms']
        self.index.index = self.corpus.index
        self.columns = columns

    def search(self, search_string):
        search_terms = preprocess(search_string)
        result_index = self.index.terms.apply(lambda terms: any(i in terms for i in search_terms))
        results = self.corpus[result_index].copy().reset_index().rename(columns={'index':'paper'})
        return SearchResults(results, self.columns + ['paper'])

'''
Creating a search index - Using a RankBM25 Search Index
We will create a simple search index that will just match search tokens in a document. 
First we tokenize the abstract and store it in a dataframe. 
Then we just match search terms against it.
RankBM25 is a python library that implements algorithms for a simple search index. 
https://pypi.org/project/rank-bm25/
'''

class RankBM25Index(WordTokenIndex):
    
    def __init__(self, corpus: pd.DataFrame, columns):
        super().__init__(corpus, columns)
        self.bm25 = BM25Okapi(self.index.terms.tolist())
        
    def search(self, search_string, n=4):
        search_terms = preprocess(search_string)
        doc_scores = self.bm25.get_scores(search_terms)
        ind = np.argsort(doc_scores)[::-1][:n]
        results = self.corpus.iloc[ind][self.columns]
        results['Score'] = doc_scores[ind]
        results = results[results.Score > 0]
        return SearchResults(results.reset_index(), self.columns + ['Score'])