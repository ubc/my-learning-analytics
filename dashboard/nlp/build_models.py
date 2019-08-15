import logging
import os

import gensim
import numpy as np
import pandas as pd
import nltk
from django.db import connections as conns
from django.db.models import Q

from django.conf import settings
from django.utils.html import strip_tags
from html import unescape
from dashboard.models import Account

logger = logging.getLogger(__name__)
wn = nltk.stem.WordNetLemmatizer()

NUMBER_OF_LAST_N_SENTENCES = 5

class DiscussionCorpus(object):
    def __init__(self, model_id, dictionary=None, tfidf_model=None, lda_model=None):
        self.model_id = model_id
        self.dictionary = dictionary
        self.tfidf_model = tfidf_model
        self.lda_model = lda_model

    def set_dictionary(self, dictionary):
        self.dictionary = dictionary

    def set_tfidf_model(self, tfidf_model):
        self.tfidf_model = tfidf_model

    def set_lda_model(self, lda_model):
        self.lda_model = lda_model

    def __iter__(self):
        accounts = Account.objects.filter(
            Q(id__in=[112240000000000267])
            # Q(id__in=self.parent_account_ids) | Q(subaccount1_id__in=self.parent_account_ids) |
            # Q(subaccount2_id__in=self.parent_account_ids) | Q(subaccount3_id__in=self.parent_account_ids) |
            # Q(subaccount4_id__in=self.parent_account_ids) | Q(subaccount5_id__in=self.parent_account_ids) |
            # Q(subaccount6_id__in=self.parent_account_ids) | Q(subaccount7_id__in=self.parent_account_ids) |
            # Q(subaccount10_id__in=self.parent_account_ids) | Q(subaccount11_id__in=self.parent_account_ids) |
            # Q(subaccount12_id__in=self.parent_account_ids) | Q(subaccount13_id__in=self.parent_account_ids) |
            # Q(subaccount14_id__in=self.parent_account_ids) | Q(subaccount15_id__in=self.parent_account_ids)
        )
        #logger.info(f"accounts: {accounts}")
        account_ids = [account.id for account in accounts]
        #logger.info(f"account_ids: {account_ids}")

        #parent_account_ids = [112240000000000267] #112240000000000267

        if len(account_ids) > 0:
            with conns['DATA_WAREHOUSE'].cursor() as cursor:
                account_ids_str = ','.join([str(account_id) for account_id in account_ids])

                cursor.execute(f"""
                    with course_info as (select cd.id, cd.account_id
                                    from course_dim cd
                                    where account_id in ({account_ids_str}) and workflow_state in ('available', 'claimed', 'created', 'completed')),
                    topic_info as (select dtf.discussion_topic_id, dtf.assignment_id, dtf.group_id
                                    from discussion_topic_fact dtf join course_info ci on ci.id = dtf.course_id),
                    topic_more as (select ti.discussion_topic_id as topic_id, null as entry_id, dtd.message
                                    from discussion_topic_dim dtd join topic_info ti on dtd.id = ti.discussion_topic_id
                                    where dtd.type is null and dtd.workflow_state in ('locked', 'active')),
                    entry_info as (select tm.topic_id, def.discussion_entry_id
                                    from discussion_entry_fact def join topic_more tm on def.topic_id = tm.topic_id)
                    select * from topic_more
                    UNION
                    select ei.topic_id, ei.discussion_entry_id as entry_id, ded.message
                    from discussion_entry_dim ded join entry_info ei on ded.id = ei.discussion_entry_id
                    where ded.workflow_state = 'active'
                    limit 20
                """)
                chunk = cursor.fetchmany(size=10)
                while chunk:
                    logger.info(f"chunk: {chunk}")
                    for row in chunk:
                        tokenized_document = _process_message(row[2])
                        if len(tokenized_document) == 0:
                            continue

                        if self.lda_model and self.tfidf_model and self.dictionary:
                            yield self.lda_model[self.tfidf_model[self.dictionary.doc2bow(tokenized_document)]]
                        elif self.tfidf_model and self.dictionary:
                            yield self.tfidf_model[self.dictionary.doc2bow(tokenized_document)]
                        elif self.dictionary:
                            yield self.dictionary.doc2bow(tokenized_document)
                        else:
                            yield tokenized_document

                    chunk = cursor.fetchmany(size=10)

def build_discussion_model(model_id):
    if not os.access(settings.NLP_MODEL_DIRECTORY, os.W_OK):
        logger.error(f"Cannot build NLP models. Folder {settings.NLP_MODEL_DIRECTORY} not writable")
        return

    model_id = 1

    # ensure the model directory exists so we can later save the models
    if not os.path.exists(_model_directory(model_id)):
        os.makedirs(_model_directory(model_id))

    corpus = DiscussionCorpus(model_id)

    # Build the dictionary (requires running though all the messages)
    dictionary = gensim.corpora.Dictionary(corpus)
    dictionary.save(_dictionary_file(model_id))
    corpus.set_dictionary(dictionary)

    # Build the tfidf model
    # uses the dictionary to saves having to run through all the messages for this model
    tfidf_model = gensim.models.TfidfModel(dictionary=dictionary)
    tfidf_model.save(_tfidf_file(model_id))
    corpus.set_tfidf_model(tfidf_model)

    # Build the lda model (requires running though all the messages)
    np.random.seed(42)
    with (np.errstate(divide='ignore')): # ignore divide-by-zero warnings
        lda_model = gensim.models.ldamodel.LdaModel(
            corpus=corpus,
            id2word=dictionary,
            num_topics=100,
            random_state=42
        )
    lda_model.save(_lda_file(model_id))
    #corpus.set_lda_model(lda_model)

def _model_directory(model_id):
    return f"{settings.NLP_MODEL_DIRECTORY}/{model_id}/"

def _dictionary_file(model_id):
    return f"{settings.NLP_MODEL_DIRECTORY}/{model_id}/dictionary.gz"

def _tfidf_file(model_id):
    return f"{settings.NLP_MODEL_DIRECTORY}/{model_id}/tfidf.gz"

def _lda_file(model_id):
    return f"{settings.NLP_MODEL_DIRECTORY}/{model_id}/lda.gz"

# tokenize a discussion message
def _process_message(message):
    if not message:
        return []

    # need to clean up the message a bit (contains html, encoded characters, and encoded newlines)
    document = unescape(strip_tags(message)).replace('\\n', '\n').strip()

    if document.replace('\n', '').strip() == '':
        return []

    # tokenize the cleaned up text
    tokenized_document = _preprocess(document)

    if len(tokenized_document) == 0:
        return []

    return tokenized_document

def _preprocess(text):
    # use WordNetLemmatizer for Lemmatization and nltk.corpus.stopwords for Stopwords
    stop_words = nltk.corpus.stopwords.words('english')
    toks = gensim.utils.simple_preprocess(text, deacc=True)
    return [
        wn.lemmatize(tok, _simplify(pos)) for tok, pos in nltk.pos_tag(toks) if tok not in stop_words
    ]

def _simplify(penn_tag):
    pre = penn_tag[0]
    if (pre == 'J'):
        return 'a'
    elif (pre == 'R'):
        return 'r'
    elif (pre == 'V'):
        return 'v'
    else:
        return 'n'