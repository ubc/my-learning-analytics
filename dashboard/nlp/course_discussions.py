import logging
import re
import statistics
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
from dashboard.models import Course, DiscussionFlattened, \
    DiscussionCoherence
from dashboard.nlp.build_models import _process_message, _dictionary_file, \
    _tfidf_file, _lda_file

logger = logging.getLogger(__name__)
wn = nltk.stem.WordNetLemmatizer()

NUMBER_OF_LAST_N_SENTENCES = 5

def process_course_discussions(prefixed_course_id):
    # TODO:
    # skip if discussion view is disabled
    # if '' in settings.VIEWS_DISABLED:
    #     return

    # Check if course exists
    try:
        course = Course.objects.get(id=prefixed_course_id)
    except Course.DoesNotExist:
        logger.info(f"Course does not exist course {prefixed_course_id}")
        return

    # TODO:
    # skip if discussion view is disabled for the course

    model_id = 1

    # Get canvas discussion topics
    topics = DiscussionFlattened.objects.filter(
        Q(course_id=course.id),
        Q(entry_id=None),
    )

    # For each topic, get the coherence for each message
    for topic in topics:
        process_course_topic_discussion(model_id, topic.topic_id)
        #async_task(process_course_topic_discussion, model_id, topic.topic_id)

def process_course_topic_discussion(model_id, topic_id):
    # skip if NLP_MODEL_DIRECTORY is not readable
    if not os.access(settings.NLP_MODEL_DIRECTORY, os.R_OK):
        logger.error(f"Cannot process course discussions for topic {topic_id}. Folder {settings.NLP_MODEL_DIRECTORY} not readable")
        return
    # skip if models don't exist
    if not os.path.exists(_dictionary_file(model_id)):
        logger.error(f"Cannot process course discussions for topic {topic_id}. Dictionary file for model {model_id} does not exist.")
        return
    if not os.path.exists(_tfidf_file(model_id)):
        logger.error(f"Cannot process course discussions for topic {topic_id}. Tfidf file for model {model_id} does not exist.")
        return
    if not os.path.exists(_lda_file(model_id)):
        logger.error(f"Cannot process course discussions for topic {topic_id}. LDA file for model {model_id} does not exist.")
        return

    # Get all discussion messages and pre-existing coherences for the topic
    entries = DiscussionFlattened.objects.filter(
        Q(topic_id=topic_id)
    )
    discussion_coherences = DiscussionCoherence.objects.filter(
        Q(topic_id=topic_id)
    )

    # load the models
    dictionary = gensim.corpora.Dictionary.load(_dictionary_file(model_id))
    tfidf_model = gensim.models.TfidfModel.load(_tfidf_file(model_id))
    lda_model = gensim.models.ldamodel.LdaModel.load(_lda_file(model_id))

    # setup a dictionary for quickly referencing the original discussion message db objects
    # and their tokenized sentences
    entry_dict = {
        entry.entry_id: entry for entry in entries
    }
    entry_sentences_dict = {
        entry.entry_id: _process_sentences(lda_model, tfidf_model, dictionary, entry.message)
        for entry in entries
    }

    new_discussion_coherences = []
    for entry in entries:
        # sliding window inspired by https://github.com/DTRPVisualDiagnostics/DTRS11-LSA
        last_n_sentences = _get_last_n_sentences(
            entry_dict, entry_sentences_dict,
            entry, NUMBER_OF_LAST_N_SENTENCES
        )
        coherences = []
        for sentence in entry_sentences_dict.get(entry.entry_id):
            weight_index = 1
            sim_lda = 0
            weight_normalizer = 0
            # Compare against the last N sentences with weighting the further away it is
            for prev_sentence in last_n_sentences:
                sim_lda += 1/weight_index * gensim.matutils.cossim(sentence, prev_sentence)
                weight_normalizer += 1/weight_index
                weight_index += 1

            if weight_normalizer > 0:
                sim_lda /= weight_normalizer

            # update last_n_sentences for next sentence
            last_n_sentences.insert(0, sentence)
            if len(last_n_sentences) > NUMBER_OF_LAST_N_SENTENCES:
                del last_n_sentences[-1]

            coherences.append(sim_lda)

        # average the coherency of each sentence in the message
        coherence = statistics.mean(coherences) if len(coherences) > 0 else 0

        # update the db with result message coherence if already exists
        # else add to new_discussion_coherences to bulk insert
        discussion_coherence = next((
            dc for dc in discussion_coherences
            if dc.topic_id == entry.topic_id and dc.entry_id == entry.entry_id
        ), None)
        if discussion_coherence:
            if discussion_coherence.coherence != coherence:
                discussion_coherence.coherence = coherence
                discussion_coherence.save()
        else:
            new_discussion_coherences.append(DiscussionCoherence(
                topic_id=entry.topic_id,
                entry_id=entry.entry_id,
                coherence=coherence
            ))

    if len(new_discussion_coherences) > 0:
        DiscussionCoherence.objects.bulk_create(new_discussion_coherences)

def _process_sentences(lda_model, tfidf_model, dictionary, message):
    if not message:
        return []

    # need to clean up the message a bit (contains html, encoded characters, and encoded newlines)
    document = unescape(strip_tags(message)).replace('\\n', '\n').strip()
    # split sentences by newlines, '?', '!', and '.'
    # (due to the way canvas discussion messages are entered, new lines are new paragraphs and
    # should be treated as new sentences in case the user forgot to add a proper line endings)
    sentences = re.split('\r?\n|\?|\!|\.', document)

    processed_sentences = []
    for sentence in sentences:
        if sentence.strip() == '':
            continue

        # Tokenize the sentance
        tokenized_sentence = _process_message(sentence.strip())
        if len(tokenized_sentence) == 0:
            continue

        # and run it through the tfidf and LDA models so it only needs to be done once
        processed_sentences.append(
            lda_model[tfidf_model[dictionary.doc2bow(tokenized_sentence)]]
        )
    return processed_sentences

# recursively search for the last n sentences relative to current_entry
def _get_last_n_sentences(entry_dict, sentence_dict, current_entry, n, current_sentences=[]):
    entry_id = current_entry.entry_id
    parent_entry_id = current_entry.parent_entry_id
    # Due to the fact that Canvas conversations can be liner or nested reply style
    # conversations, we must check the parent_entry_id (or topic message) for previous sentences
    # (can't rely on order)

    # check if there is a parent entry to current entry
    if parent_entry_id and parent_entry_id in entry_dict:
        parent_entry = entry_dict.get(parent_entry_id)
        parent_sentences = sentence_dict.get(parent_entry_id)

    # check if the parent is the topic root
    elif entry_id and not parent_entry_id:
        parent_entry = entry_dict.get(None)
        parent_sentences = sentence_dict.get(None)

    # else this is the topic root (return since there are no more sentences)
    else:
        return current_sentences

    if parent_sentences and len(parent_sentences) > 0:
        # add the sentences in order of most recent first
        current_sentences += reversed(parent_sentences)

    # check if done
    if len(current_sentences) >= n:
        return current_sentences[:n]

    # check parent for more
    return _get_last_n_sentences(entry_dict, sentence_dict, parent_entry, n, current_sentences)
