# Name: index.py
# Since: 03/24/2019
# Author: Christen Ford
# Purpose: Runs Map/Reduce on the database to generate the inverted index

from pymongo import MongoClient
from bson.code import Code

# define the map function
# note the paradigm is that each Map node runs exactly the same code
#   across a different piece of the dataset to map keys to values and emit
#   the result in some sorted order
# this function should take a set of eBooks and map each docs bookid (or
#   _objectid) to the frequency count for each word in the document
# the map should be: string -> array of pairs, where each pair consists of 
#   the term and its frequency, the array should be sorted first 
#   alphabetically by the term, and then numerically by frequency
map_index = Code(
        '''
        function () {
            
        }
        ''')

# define the reduce function
# note: the paradigm functions the same as above, except that the 
#   reduce function brings all of the data emitted in the map stage intto a 
#   single, locally sorted dataset
reduce_index = Code(
        '''
        function () {

        }
        ''')
