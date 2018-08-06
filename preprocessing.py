import csv
import sys
import spacy
import nltk
import en_core_web_sm
import re
import gensim

# Increase capacity of csv file
csv.field_size_limit(sys.maxint)

# Import modules from another directory
reload(sys)
sys.path.append('/Users/kawoo/PycharmProjects/')
sys.path.insert(0, '/Users/kawoo/PycharmProjects')

# Modules for text preprocessing
from stop_words import get_stop_words
from gensim import corpora
from nltk.tokenize import word_tokenize
from nltk.stem.porter import PorterStemmer
from nltk.stem.wordnet import WordNetLemmatizer
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger') # For POS tagging
nltk.download('wordnet')

class Preprocessing(object):
    ''' Perform preprocessing steps on dataset. '''

    def __init__(self):
        self.stop_words = nltk.corpus.stopwords.words('english')
        self.stemmer = PorterStemmer()
        self.lemmatizer = WordNetLemmatizer()
        self.stops_english = get_stop_words('english')
        self.stops_portuguese = get_stop_words('portuguese')
        self.stops_russian = get_stop_words('russian')
        self.stops_spanish = get_stop_words('spanish')
        self.stops_norwegian = get_stop_words('norwegian')
        self.stops_french = get_stop_words('french')
        self.is_english = set(nltk.corpus.words.words())



    def remove_null(self, dataframe):
        ''' Helper function to remove NA values. '''
        dataframe = dataframe.dropna(axis = 0, how = 'any')
        return dataframe

    def preprocess_text(self, text_area):
        ''' Function to preprocess text data. Steps taken are:
            1. Tokenization
            2. Removal of any non alphanumeric character
            3. Lowercase words
            4. Removal of stop words
            5. Bigram / Trigram collocation detection (/frequently co-occurring tokens) using Gensim's Phrases
            6. Lemmatization (not stemming to avoid reduction of interpretability

            Parameters: list of strings
            ----------
            Returns: Preprocessed list of strings.
            -------
        '''
        text_area = [line.encode('utf-8') for line in text_area] # for encoding problems
        text_area = [unicode(line, errors = 'ignore') for line in text_area] # for encoding problems
        text_area = [word_tokenize(line) for line in text_area] # tokenization
        text_area = [[word for word in line if len(word) > 1] for line in text_area] # remove single character strings
        text_area = [[word for word in line if word.isalnum()] for line in text_area] # remove punctuation
        text_area = [[word.lower() for word in line] for line in text_area] #lowercase
        text_area = [[word for word in line if word in self.is_english] for line in text_area] # remove non-English
        text_area = [[word for word in line if not word in self.stop_words] for line in text_area] # remove English stopwords
        text_area = [[word for word in line if not word in self.stops_spanish] for line in text_area] # remove Spanish stopwords
        text_area = [[word for word in line if not word in self.stops_russian] for line in text_area] # remove Russian stopwords
        text_area = [[word for word in line if not word in self.stops_portuguese] for line in text_area] # remove Portuguese stopwords
        text_area = [[word for word in line if not word in self.stops_norwegian] for line in text_area] #remove Norwegian stopwords
        text_area = [[word for word in line if not word in self.stops_french] for line in text_area] # remove French stopwords
        text_area = [line for line in text_area if line != []]
        text_area = self.make_n_grams(text_area, n_gram = 'bigram') # bigram
        text_area = self.make_n_grams(text_area, n_gram = 'trigram') # trigram
        text_area = self.pruning(text_area, 'lemmatization') # prune words using lemmatization
        text_area = self.remove_rare_words(text_area) # remove words that appear too rarely
        return text_area

    def remove_rare_words(self, text_area):
        ''' Remove least common words for pattern detection across texts.
        Helpful for not overfitting. '''
        flat_list_of_tokens = [word for line in text_area for word in line]
        frequent_distribution = nltk.FreqDist(flat_list_of_tokens)
        rare_words = frequent_distribution.keys()[-300:]
        text_area = [[word for word in line if not word in rare_words] for line in text_area]
        return text_area

    def pruning(self, text_area, pruning_method = ''):
        ''' Prune words to reduce them to their most basic form. '''
        if pruning_method == 'stemming':
            text_area = [[self.stemmer.stem(word) for word in line] for line in text_area]
        elif pruning_method == 'lemmatization':
            text_area = [[self.lemmatizer.lemmatize(word) for word in line] for line in text_area]
        else:
            raise ValueError('Please set pruning_method to "stemming" or "lemmatization".')
        return text_area


    def make_n_grams(self, text_area, n_gram = ''):
        # build bigram/trigram models
        bigram = gensim.models.Phrases(text_area, min_count = 5, threshold = 100)
        trigram = gensim.models.Phrases(bigram[text_area], threshold = 100)
        # faster way to get a sentence clubbed as a bigram/trigram
        bigram_mod = gensim.models.phrases.Phraser(bigram)
        trigram_mod = gensim.models.phrases.Phraser(trigram)
        if n_gram == 'bigram':
            return [bigram_mod[doc] for doc in text_area]
        elif n_gram == 'trigram':
            return [trigram_mod[bigram_mod[doc]] for doc in text_area]



