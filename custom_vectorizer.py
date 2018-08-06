from nltk.corpus import wordnet
from nltk import pos_tag
from sklearn.feature_extraction.text import CountVectorizer
from preprocessing import Preprocessing

preprocessing = Preprocessing()

class OwnCountVectorizer(CountVectorizer):
    ''' This class has been created to palliate to two problems found in Sklearn's vectorizer:
    - there is no in-built lemmatizer in Sklearn's vectorizer
    - the list of stop words only applies for the English language.

    In this custom vectorizer, we have used concepts of Object Oriented Programming by inheriting
    and subclassing the original Sklearn's CountVectorizer class, and overwritten the build_analyzer
    and get_stop_words methods by implementing the lemmatizer for each list in the raw text matrix,
    and filtering out Norwegian, Portuguese, Russian, Spanish and French stop words. '''

    def get_wordnet_pos(self, treebank_tag):
        ''' WordNet's lemmatizer requires the second keyword argument "pos" to be given for proper lemmatization.
        Problem: NLTK's part of speech tagger outputs tags that are not compatible with WordNet's lemmatizer, e.g:
        NLTK pos_tag: 'NN' ; WordNet: 'n'.
        Hence this function. It converts NLTK's part of speech tagger's output to WordNet compatible tags. '''
        if treebank_tag.startswith('J'):
            return wordnet.ADJ
        elif treebank_tag.startswith('V'):
            return wordnet.VERB
        elif treebank_tag.startswith('N'):
            return wordnet.NOUN
        elif treebank_tag.startswith('R'):
            return wordnet.ADV
        else:
            return wordnet.NOUN

    def build_analyzer(self):
        ''' The vectorization of words will now include lemmatization as well. '''
        analyzer = super(OwnCountVectorizer, self).build_analyzer()
        return lambda doc: (preprocessing.lemmatizer.lemmatize(word = w, pos = self.get_wordnet_pos(pos_tag([w])[0][1])) for w in analyzer(doc))

    def get_stop_words(self):
        ''' When kwarg stop_words has value "english", all other stop words will also be removed. '''
        english_stop_words = super(OwnCountVectorizer, self).get_stop_words()
        all_stop_words = preprocessing.stops_norwegian + preprocessing.stops_portuguese + \
                      preprocessing.stops_russian + preprocessing.stops_spanish + \
                      preprocessing.stops_french + list(english_stop_words)
        return all_stop_words

