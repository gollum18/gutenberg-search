import pymongo
import os
import re
import snowballstemmer
import string
import sys

from io import StringIO
from threading import Thread

import pg_funcs

# create a trannslator for replacing punctuation with a space
translator = str.maketrans({c:' ' for c in string.punctuation})

# get a global stemmer object
stemmer = snowballstemmer.stemmer('english')

# create a stemming alphabet, characters in words not this string are 
#   are filtered out before the word is stemmed
# the allowable alphabet is 'a-z'
alphabet = string.ascii_lowercase

# the various headers that appear in the ebook files
headers = {
    'Title: ': 'title',
    'Author: ': 'author',
    'Translator ': 'translator',
    'Last updated: ': 'last_updated',
    # these two guys seem to be conflicting? some ebooks only contain
    #   a release date, some a posting date, others both
    # Its clear that the posting date is the date the book was 
    #   publised on pg, but the release date either means the 
    #   same thing or it is genuinely the release date of the book/work.
    # this seems to be dependent on the time the book was released on
    #   pg, at some point they must have underwent a format change 
    #   between release/posting dates that did not propagate to their 
    #   entire collection of ebooks leading to the inconsistency
    #   between the meaning of the two dates
    'Release Date: ': 'release_date',
    'Posting Date: ': 'posting_date',
    'Language: ': 'language',
    # this is generally true, however some books marked ascii are 
    #   actually encoded in iso-8859-1 (western), leading to the mess 
    #   below that I use to catch them
    'Character set encoding: ': 'char_set',
    # this guy catches a typo I dont want to correct on the fly
    'Chatacter set encoding: ': 'char_set',
    # this guy is generally true but some texts announce the publisher 
    #   slightly different
    'Produced by ': 'publisher'
}



'''
Extracts the value from a line corresponding to a given key.
'''
def extract_value(key, line):
    return line.replace(key, '').strip('\r\n')

class EBookParser(Thread):

    '''
    Creates a new EBookParser thread that parses the ebook stored 
    at the specified filename.
        filename: The address of the book on disk.
    '''
    def __init__(self, filepath):
        Thread.__init__(self)
        self.filepath = filepath
        # these can only be retrieved once the thread is dead
        #   check thread.is_alive() for false, otherwise youll be 
        #   dissapointed when querying these
        # alternatively create the thread then join() on it, execution
        #   will resume immediately following the line after the join
        #   when the threads run() method completes, you can query 
        #   these at that point
        self.book = dict()
        self.stems = []

    '''
    Overridden run() method inherited from the Thread class. Does the 
    work of parsing each book. 
    '''
    def run(self):
        # try to open the file in utf-8, ascii, or iso-8895-1
        #   if theres an error, print out the filename
        # this is ugly and not the best solution, but the best I can think
        #   of right now to deal with the varying encodings
        # not sure if the three finallys are necessary or if I could 
        #   use just one, but its fine
        # yup: this entire thing just opens the file in the proper format
        #   if anyone else has a way to deal with multiple unknown file 
        #   encodings in Python, please let me know (without using 
        #   statistical methods to guess the encoding please, I tried,
        #   its only a marginally good option)
        try:
            raw_data = None
            try:
                f = open(self.filepath)
                raw_data = f.read()
            except UnicodeDecodeError:
                try:
                    f = open(self.filepath, encoding='ascii')
                    raw_data = f.read()
                except UnicodeDecodeError:
                    try:
                        f = open(self.filepath, encoding='iso-8859-1')
                        raw_data = f.read()
                    except UnicodeDecodeError:
                        print('Unknown encoding for:', self.filepath)
                        return
            if f:
                f.close()
            # get the book id and filepath
            self.book['bookid'] = pg_funcs.extract_bookid(self.filepath)
            self.book['filepath'] = self.filepath
            # 0 = header, 1 = content, 2 = footer
            state = 0
            for line in StringIO(raw_data):
                # check if we need to advance state
                if line.startswith('*** START'):
                    state = 1
                    continue
                elif line.startswith('*** END'):
                    state = 2
                    continue
                # pull information from the header
                if state == 0:
                    for text_key, json_key in headers.items():
                        if text_key in line:
                            self.book[json_key] = extract_value(text_key, line)
                # stem the content
                elif state == 1:
                    # clean the line of all punctuation
                    line = line.translate(translator)
                    # get the words
                    for word in line.split(' '):
                        # lowercase the word
                        word = word.lower()
                        # clean the word
                        word = ''.join([c for c in word if c in alphabet])
                        # add the word to the stems list
                        self.stems.append(stemmer.stemWord(word))
                # ignore the footer
                elif state == 2:
                    break
        except IOError:
            print('An IOError occured processing file:', self.filename)
        # clear out the whitespace in the stems
        self.stems = ' '.join(' '.join(self.stems).split())

def print_help():
    print('-'*80)
    print('Parses eBooks from the Project Gutenberg e-library.')
    print('EBooks are expected to be in *.txt format.')
    print('Other formats will not be parsed.')
    print('The user must supply the directory where they are stored.')
    print('-'*80)
    print('usage: python convert.py [dir]')

'''
Main method, called when the program executes.
    root: the root directory that the ebook files are stored in
'''
def main():
    if len(sys.argv) < 2:
        print('Error: You did not specify a directory for the eBooks!')
        print_help()
        sys.exit(22)
    if sys.argv[1] == '-h' or sys.argv[1] == '--help':
        print_help()
        sys.exit(0)
    elif not os.path.isdir(sys.argv[1]):
        print('Error: Specified file is not a directory!')
        print_help()
        sys.exit(2)
    # open mongodb client on default host and port
    client = pymongo.MongoClient()
    db = client.pgdb
    for filename in pg_funcs.get_files(sys.argv[1]):
        t = EBookParser(filename)
        t.start()
        t.join()
        db.books.insert_one(t.book)
        if not os.path.exists(os.path.join('data', 'stems')):
            os.mkdir(os.path.join('data', 'stems'))
        with open(os.path.join('data', 'stems', t.book['bookid']+'.txt'), 'w') as stemfile:
            for stem in t.stems:
                stemfile.write(stem)
    client.close()

if __name__ == '__main__':
    main()
