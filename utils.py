import logging
from pathlib import Path
import numpy as np
import pandas as pd
from difflib import SequenceMatcher


# Define similarity function
def similar(a, b):
    """
    similar compares two strings 'a' and 'b' and returns their similarity ratio
    Inputs:
        a: first string
        b: second string
    Outputs:
        similarity: similarity ratio
    """
    return SequenceMatcher(None, a, b).ratio()


# Define similarity function
def similar_multi(a, b, thr=0.8):
    """
    similar compares two strings 'a' and 'b', computes the similarity matrix
    S with dim(S) = (words in a) x (words in b) that is the similarity ratio of
    every word in 'a' when compared with every word in 'b' and returns the
    summation of ratios over the shortest dimension (minimum length of words(a,b))
    Inputs:
        a: first string
        b: second string
    Outputs:
        similarity: sum of similarity ratios calculated over the shortest
            dimension
    """
    # Length in words of 'a'
    LA = len(a.split())
    # Length in words of 'b'
    LB = len(b.split())
    # Initialize S matrix
    similarity = np.zeros((LA, LB))
    # Calculate similarity ratios for every pair of words a_i, b_j
    for idxA, wordA in enumerate(a.split()):
        for idxB, wordB in enumerate(b.split()):
            similarity[idxA, idxB] = similar(wordA, wordB)
    # Apply similarity ratio threshold
    similarity[similarity < thr] = 0
    # Calculate the sum over the shortest distance
    similarity = np.sum(np.max(similarity, axis=np.argmin([LA, LB])))
    return similarity


# Remove non-ascii characters from string
def removeNonAscii(s): return "".join(i for i in s if ord(i) < 128)


def unique_list_elements(input_list):
    return list(set(input_list))


def list_to_dict(mapping_list):
    mapping_dict = dict()
    for k, v in mapping_list.items():
        for i in v:
            mapping_dict[i] = k
    return mapping_dict



def remove_greek_accents(df, col):
    accents_list={'Ά':'Α', 'Έ':'Ε', 'Ό':'Ο', 'Ί':'Ι', 'Ύ':'Υ', 'Ή':'Η', 'Ώ': 'Ω'}
    for k, v in accents_list.items():
        logging.info(f'Replace vowel with accent {k} with {v}')
        df[col] = df[col].str.replace(k, v)
    return df