import pandas as pd
import numpy as np
import os
import re
import operator
import matplotlib.pyplot as plt
import warnings
import gensim.models
import pyLDAvis.gensim
import pyLDAvis.sklearn
import nltk
import pickle
warnings.filterwarnings('ignore', category = DeprecationWarning) # not paying heed to them for now

from gensim.models import CoherenceModel, LdaModel, LsiModel, HdpModel
from gensim.models.wrappers import LdaMallet
from gensim.corpora import Dictionary
from gensim.matutils import argsort
from gensim import corpora, models, similarities
from gensim.topic_coherence import segmentation, probability_estimation, direct_confirmation_measure, aggregation,indirect_confirmation_measure
from pprint import pprint
from collections import namedtuple
from sklearn.decomposition import LatentDirichletAllocation
from preprocessing import Preprocessing
from sklearn.model_selection import GridSearchCV
from custom_vectorizer import OwnCountVectorizer

# nltk.download('words')

preprocessing = Preprocessing()

def prepare_data(filename):
    ''' Load and prepare the data for topic modeling. '''
    print 'Loading dataset...'
    data = pd.read_csv(filename, encoding = 'utf-8')
    data = preprocessing.remove_null(data)
    print 'Dataset loaded'
    print 'Preparing text inputs...'
    texts = preprocessing.preprocess_text(texts)
    titles = preprocessing.preprocess_text(titles)
    titles = titles[0:len(texts)]
    text_input = concat_text_input(titles, texts)
    text_data = data['scraped_title'] + ' ' + data['scraped_content']
    return text_input, text_data

def concat_text_input(titles, texts):
    ''' Concatenate titles and texts. '''
    n_sentences = len(titles)
    titles_texts_list = list()
    sequence_length = list()
    for i in range(n_sentences):
        titles_texts_list.append(titles[i] + texts[i])
        sequence_length.append(len(titles_texts_list[i]))
    return titles_texts_list

def create_dictionary_and_corpus(tokens):
    ''' Function to create and return a dictionary and a corpus from the tokens. '''
    print 'Creating a dictionary...'
    dictionary = Dictionary(tokens)
    dictionary.filter_extremes(no_below = 5, no_above = 0.7) # filter out words that occur in less than 50 documents, or more than 70% of the documents
    print 'Creating a corpus...'
    corpus = [dictionary.doc2bow(token) for token in tokens]
    print 'Number of unique tokens to train on: %d' % len(dictionary)
    print 'Number of documents to train on: %d' % len(corpus)
    return dictionary, corpus

def evaluate_graph(dictionary, corpus, texts, iterations, passes, min_topic, max_topic, coherence):
    '''
    Function to display the number of topics - LDA graph using coherence values.
    Parameters: dictionary (Gensim's dictionary)
                corpus (Gensim's corpus)
                limit: topic limit
    Returns: models_list: a list of topic models generated by LDA
             coherence_values = coherence values corresponding to the LDA model with respective number of topics
    '''
    coherence_values = list()
    models_list = list()
    for num_topics in range(min_topic, max_topic + 1):
        model = latent_dirichlet_allocation(corpus = corpus, num_topics = num_topics, id2word = dictionary, iterations = iterations, passes = passes)
        models_list.append(model)
        coherence_model = CoherenceModel(model = model, texts = texts, dictionary = dictionary, coherence = coherence)
        coherence_values.append(coherence_model.get_coherence())

    # Plot graph
    x = range(min_topic, max_topic + 1)
    plt.plot(x, coherence_values)
    plt.xlabel('Number of topics')
    plt.ylabel('Coherence score')
    plt.legend(('coherence value'), loc = 'best')
    plt.show()

    return models_list, coherence_values

def return_top_model():
    '''
    LDA: probabilistic model that comes up with different topics each time we run it.
    To control the quality of the topic model produced, we check what the interpretability
    of the best topic is and keep evaluating the topic model, until the threshold is crossed.
    Returns: model: final evaluated topic model
             top_topics: ranked topics in decreasing order (type: list of tuples). 
    '''
    top_topics = [(0,0)]
    while top_topics[0][1] < 0.97:
        model = latent_dirichlet_allocation(corpus = corpus, id2word = dictionary)
        coherence_values = dict()
        for n, topic in model.show_topics(num_topics = -1, formatted = False):
            topic = [word for word, _ in topic]
            coherence_model = CoherenceModel(topics = [topic], texts = text_input, dictionary = dictionary, window_size = 10)
            coherence_values[n] = coherence_model.get_coherence()
        top_topics = sorted(coherence_values.items(), key = operator.itemgetter(1), reverse = True)
    return model, top_topics

def evaluate_bar_graph(coherences, indices):
    '''
    Function to plot bar graph.
    Parameters: coherences: list of coherence values
                indices: indices to be used to mark bars.
                /!\ length of the two parameters should be equal!
    '''
    assert len(coherences) == len(indices)
    n = len(coherences)
    x = np.arrange(n)
    plt.bar(x, coherences, width = 0.2, tick_label = indices, align = 'center')
    plt.xlabel('Models')
    plt.ylabel('Coherence value')

def reload_variables(filepath, *args):
    ''' Reload pickled variables. '''
    for variable in list(args):
        variable = pickle.load(open('filename' + variable + '.p', 'rb'))
    return variable

def latent_semantic_indexing(corpus, num_topics, id2word):
    ''' LATENT SEMANTIC INDEXING
    # Advantage of LSI: ranks topics by itself. Outputs topics in a ranked order.
    # Requires a num_topics parameter (200 by default) to determine the number of latent dimensions after the SVD.
    '''
    print 'Latent Semantic Indexing'
    lsi_model = LsiModel(corpus = corpus, num_topics = num_topics, id2word = id2word)
    lsi_model.show_topics(num_topics = num_topics)
    lsi_topic = lsi_model.show_topics(formatted = False)
    return lsi_model

def hierarchical_dirichlet_process(corpus, num_topics, id2word):
    ''' HIERARCHICAL DIRICHLET PROCESS
    # Advantage of HDP: fully unsupervised: can determine the ideal number of topics it needs through posterior inference
    '''
    print 'Hierarchical Dirichlet Process'
    hdp_model = HdpModel(corpus = corpus, id2word = id2word)
    hdp_model.show_topics()
    hdp_topic = hdp_model.show_topics(formatted = False)
    return hdp_model

def LDA_gensim(corpus, num_topics, id2word, passes, iterations, coherence):
    ''' LATENT DIRICHLET ALLOCATION
    # Generative model that assumes each document is a mixture of topics, each topic is a mixture of words.
    '''
    print 'Latent Dirichlet Allocation'
    #id2word = id2word.id2token # make an index to word dictionary
    lda_model = LdaModel(corpus = corpus, num_topics = num_topics, id2word = id2word, passes = passes, iterations = iterations)
    lda_topics = lda_model.show_topics(formatted = False)
    # compute coherence score
    coherence_model = CoherenceModel(model = lda_model, texts = text_input, dictionary = id2word, coherence = coherence)
    coherence_lda = coherence_model.get_coherence()
    print('\nCoherence Score: ', coherence_lda)
    return lda_model

def LDA_sklearn(text_data, num_topics, iterations, visualization = False, gridsearch = False ):
    vectorizer = OwnCountVectorizer(max_df = 0.95, min_df = 2, stop_words = 'english', lowercase = True,
                                    token_pattern = '[a-zA-Z\-][a-zA-Z\-]{2,}', ngram_range = (2, 3),
                                    decode_error = 'ignore')
    vectorized_text_data = vectorizer.fit_transform(text_data)
    lda_model = LatentDirichletAllocation(n_topics = num_topics, max_iter = iterations, learning_method = 'online',
                                          random_state = 100, batch_size = 120, evaluate_every = -1, n_jobs = -1)
    lda_output = lda_model.fit_transform(vectorized_text_data)
    print lda_model # model attributes
    print 'Log likelihood: ', lda_model.score(vectorized_text_data) # log-likelihood: the higher the better
    print 'Perplexity: ', lda_model.perplexity(vectorized_text_data) # perplexity = exp(-1. * log-likelihood per word, the lower the better
    pprint(lda_model.get_params()) # see model parameters

    # GridSearch the best model
    search_params = {'n_components': [41, 45, 50, 55, 60], 'learning_decay': [.5, .7, .9]}
    lda = LatentDirichletAllocation() # initialize the model
    model = GridSearchCV(lda, param_grid = search_params) # initialize the gridsearch class
    model.fit(vectorized_text_data) # do the grid search

    best_lda_model = model.best_estimator_ # best model
    print 'Best parameters: ', model.best_params_ # best parameters
    print 'Best Log-likelihood score: ', model.best_score_
    print 'Model perplexity: ', best_lda_model.perplexity(vectorized_text_data)

    # Compare LDA model performance scores

    # Get Log-likelihoods from Gridsearch otputs
    n_topics = [41, 45, 50, 55, 60]
    log_likelihoods_5 = [round(gscore.mean_validation_score) for gscore in model.cv_results_ if
                         g.score.parameters['learning_decay' == 0.5]]
    log_likelihoods_7 = [round(gscore.mean_validation_score) for gscore in model.cv_results_ if
                         g.score.parameters['learning_decay' == 0.7]]
    log_likelihoods_9 = [round(gscore.mean_validation_score) for gscore in model.cv_results_ if
                         g.score.parameters['learning_decay' == 0.9]]

    # Show graph
    plt.figure(figsize = (10, 8))
    plt.plot(n_topics, log_likelihoods_5, label = '0.5')
    plt.plot(n_topics, log_likelihoods_7, label = '0.7')
    plt.plot(n_topics, log_likelihoods_9, label = '0.9')
    plt.title('Gridsearch output on choosing optimal LDA model')
    plt.xlabel('Number of topics')
    plt.ylabel('Log likelihood scores')
    plt.legend(title = 'Learning decay', loc = 'best')
    plt.show()

    if visualize == True:
        panel = pyLDAvis.sklearn.prepare(lda_model, vectorized_text_data, vectorizer, mds = 'tsne')
        pyLDAvis.show(panel)
    else:
        return lda_output[0] # for verification that it works

def lda_mallet(corpus, num_topics, id2word, iterations, coherence):
    mallet_path = '/Users/kawoo/PycharmProjects/AutoTagging/ImportantFiles/mallet-2.0.8/mallet-2.0.8/bin/mallet'
    lda_model_mallet = gensim.models.wrappers.LdaMallet(mallet_path, corpus = corpus, num_topics = num_topics, id2word = id2word, iterations = iterations)
    # compute coherence score
    coherence_model_ldamallet = CoherenceModel(model = lda_model_mallet, texts = text_input, dictionary = id2word, coherence = coherence )
    coherence_ldamallet = coherence_model_ldamallet.get_coherence()
    print('\nCoherence Score: ', coherence_ldamallet)

def show_LDA(lda_model, corpus, dictionary):
    prepared_data = pyLDAvis.gensim.prepare(lda_model, corpus, dictionary)
    print ''' Launching webpage for visualization... '''
    pyLDAvis.show(prepared_data)

def make_pipeline():
    '''Custom topic coherence measure. '''
    print 'Making pipeline...'
    make_pipeline = namedtuple('Coherence_Measure', 'seg, prob, conf, aggr')
    measure = make_pipeline(segmentation.s_one_one, probability_estimation.p_boolean_sliding_window,
                            direct_confirmation_measure.log_ratio_measure, aggregation.arithmetic_mean)
    print 'Getting topics out of the model...'
    topics = list()
    for topic in model.state.get_lambda():
        best_n = argsort(topic, top_n = 10, reverse = True)
    topics.append(best_n)
    return topics

def topic_model_tfidf(corpus, id2word, num_topics, iterations, passes):
    ''' Perform topic modeling with TFIDF vectorization instead of BOW vectorization. '''
    tfidf = models.TfidfModel(corpus) # tfidf: read-only object that can be used to convert old BOW integer counts representations to TF-IDF real-valued weights representations.
    corpus_tfidf = tfidf[corpus]
    lda_model = LdaModel(corpus = corpus_tfidf, id2word = id2word, num_topics = num_topics, iterations = iterations, passes = passes)
    return corpus_tfidf, lda_model


if __name__ == '__main__':

    # Prepare data
    text_input, text_data = prepare_data(filename)

    # Create dictionary and corpus
    dictionary, corpus = create_dictionary_and_corpus(text_input)

    # Saving variable on disk using python package "pickle" for quicker loading in the future
    print 'Pickling process running...'
    pickle.dump(text_input, open(filepath, 'wb'))
    pickle.dump(text_input, open(filepath, 'wb'))
    pickle.dump(text_input, open(filepath, 'wb'))
    pickle.dump(dictionary, open(filepath, 'wb'))
    pickle.dump(corpus, open(filepath, 'wb'))

    print('Running models...')

    # LATENT SEMANTIC INDEXING
    LSI = latent_semantic_indexing(corpus = corpus, num_topics = 40, id2word = dictionary)

    # HIERARCHICAL DIRICHLET PROCESS
    HDP = hierarchical_dirichlet_process(corpus = corpus, num_topics = 40, id2word = dictionary)

    # LATENT DIRICHLET ALLOCATION
    # Generative model that assumes each document is a mixture of topics, each topic is a mixture of words.
    LDA = LDA_gensim(corpus = corpus, num_topics = 40, id2word = dictionary, passes = 20, iterations = 800, coherence = 'c_v')
    # show_LDA(LDA, corpus = corpus, dictionary = dictionary)

    # LDA MALLET
    LDA_MALLET = lda_mallet(corpus = corpus, num_topics = 41, id2word = dictionary, iterations = 400, coherence = 'c_v')

    # TOPIC COHERENCE
    print ('------TOPIC COHERENCE------')
    lda_models_list, coherence_values = evaluate_graph(dictionary = dictionary, corpus = corpus, texts = text_input,
                                                       iterations = 800, passes = 20, min_topic = 40, max_topic = 60,
                                                       coherence = 'c_v')

    # TOP MODELS - LDA as LSI
    model, top_topics = return_top_model()
    print 'Top topics are: {}'.format(top_topics[:5])

    # INFERENCE
    print('Inference on model...')
    pprint([model.show_topic(topicid) for topicid, coherence_values in top_topics[:10]])

    # MODELS - Evaluation
    print('Evaluation of models...')
    print('Topics...')
    lda_lsi_topics = [[word for word, probability in model.show_topic(topicid)] for topicid, coherence_values in top_topics]
    lsi_topics = [[word for word, probability in topic] for topicid, topic in lsi_topics]
    hdp_topics = [[word for word, probability in topic] for topicid, topic in hdp_topics]
    lda_topics = [[word for word, probability in topic] for topicid, topic in lda_topics]
    model_topics = [[word for word, probability in topic] for topicid, topic in model_topics]

    print('Coherence...')
    lsi_coherence = CoherenceModel(topics = lsi_topics[:10], texts = text_input, dictionary = dictionary, window_size = 10).get_coherence()
    hdp_coherence = CoherenceModel(topics = hdp_topics[:10], texts = text_input, dictionary = dictionary, window_size = 10).get_coherence()
    lda_coherence = CoherenceModel(topics = lda_topic, texts = text_input, dictionary = dictionary, window_size = 10).get_coherence()
    model_coherence = CoherenceModel(topics = model_topics, texts = text_input, dictionary = dictionary, window_size = 10).get_coherence()
    lda_lsi_coherence = CoherenceModel(topics = lda_lsi_topics[:10], texts = text_input, dictionary = dictionary, window_size = 10).get_coherence()

    # BAR GRAPH
    print('Plotting bar graph...')
    evaluate_bar_graph([lsi_coherence, hdp_coherence, lda_coherence, model_coherence, lda_lsi_coherence],
                       ['LSI', 'HDP', 'LDA', 'LDA_model', 'LDA_LSI'])


main()