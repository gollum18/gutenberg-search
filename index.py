# Name: index.py
# Since: 26/03/2019
# Author: Christen Ford
# Description: Defines the MapReduce phases needed to generate the 
#   an inverted index over the Project Gutenberg library.

import pymongo
from bson.code import Code

'''
Defines a Map/Reduce function for generating a word count over a 
document.

This is phase one in the generation of the inverted index.
'''
def phase1_word_count():

    '''
    This map function steps through a document emitting
    word, 1 key value pairs to be reduced into a word count for 
    each word.
    '''
    map = Code(
        '''
        function() {
            this.stemmings.split(" ").forEach(function(word) {
                emit(word, 1);
            });
        }
        ''')

    '''
    This reduce function takes all of the key value pairs emitted
    by the map function and reduces them to a single word/wordcount
    pair.
    '''
    reduce = Code(
        '''
        function(key, values) {
            var total = 0;
            values.forEach(function(value) {
                total += value;
            });
            return total;
        }
        ''')
