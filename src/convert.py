import pymongo
import os
import re
import snowballstemmer
import string
import sys

from io import StringIO
from threading import Thread
from threading import Lock
from threading import BoundedSemaphore

import pg_funcs

# Set this to a reasonable number for your system
_MAX_THREADS = 5

# create a trannslator for replacing punctuation with a space
translator = str.maketrans({c:' ' for c in string.punctuation})

# create a stemming alphabet, characters in words not this string are 
#   are filtered out before the word is stemmed
# the allowable alphabet is 'a-z'
alphabet = string.ascii_lowercase

# path for the stem directory
stempath = os.path.join('data', 'stems')

# the various headers that appear in the ebook files
# TODO: the better solution is to use the 're' library to extract these
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

    # stores the books seen so far, used when threaded
    books_seen = set()
    
    # used to ensure single read/write access to disk and MongoDB
    read_lock = Lock()
    write_lock = Lock()
    
    # used to limit the number of threads created
    thread_count = 0

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
        self.stemmer = snowballstemmer.stemmer('english')
        self.io_err = False

    def read_data(self):
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
                    return None
        if f:
            f.close()
        return raw_data

    '''
    Overridden run() method inherited from the Thread class. Does the 
    work of parsing each book. 
    '''
    def run(self):
        try:
            # get the book id and filepath
            self.book['bookid'] = pg_funcs.extract_bookid(self.filepath)
            self.book['filepath'] = self.filepath
            # acquire the lock
            EBookParser.read_lock.acquire()
            # read the data for the book
            raw_data = self.read_data()
            # release the lock
            EBookParser.read_lock.release()
            if not raw_data:
                print('Unable to read data for ebook,', self.filepath, 'ebook not parsed!')
                return
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
                        if not word.isspace():
                            self.stems.append(
                                self.stemmer.stemWord(word))
                # ignore the footer
                elif state == 2:
                    break
        except IOError:
            print('An IOError occured processing file:', self.filename)
            self.io_err = True
        finally:
            if not self.io_err:
                # clear out the whitespace in the stems
                self.stems = ' '.join(' '.join(self.stems).split())
                # acquire the write lock, future attempts to acquire the lock while it is already held will block the thread attemmpting to acquire it
                EBookParser.write_lock.acquire()
                # call the write method
                self.write_ebook()
                # release the write lock
                EBookParser.write_lock.release()
            # decrement the thread counter
            EBookParser.thread_count -= 1
                
        
    def write_ebook(self):
        # deal with books weve already seen, somehow this is happening, must have a duplicate book or two somewhere, also deal with books that do not declare metadata
        if self.book['bookid'] in EBookParser.books_seen or not self.stems:
            return
        # insert the book in the database
        db.books.insert_one(self.book)
        # write the stem file to disk
        write_stem_file(os.path.join(stempath, self.book['bookid']+'.txt'), self.stems)
        EBookParser.books_seen.add(self.book['bookid'])

def print_help():
    print('-'*80)
    print('Parses eBooks from the Project Gutenberg e-library.')
    print('EBooks are expected to be in *.txt format.')
    print('Other formats will not be parsed.')
    print('The user must supply the directory where they are stored.')
    print('-'*80)
    print('usage: python convert.py [dir]')

def write_stem_file(filepath, stems):
    '''
    Writes stems to the file specified with filepath.
    '''
    if not filepath:
        print('No filepath specified, stem file not written!')
        return
    if not stems:
        print('No stems specified for file at,', filepath, 'stem file not written!')
        return
    try:
        with open(filepath, 'w') as stemfile:
            for stem in stems:
                stemfile.write(stem)
    except IOError:
        print('IOError occurred while writing stem file for book at:', filepath, ', stem file not written.')

# open mongodb client on default host and port
client = pymongo.MongoClient()
db = client.pgdb
# create the index if necessary
if "books" not in db.list_collection_names():
    # create the index on the books collection
    db.books.create_index("bookid")

def does_book_exist(bookid):
    '''
    Determines if a book already exists in the book collection with the specified bookid.
    '''
    if db.books.count_documents({"bookid": {"$eq": bookid}}) > 0:
        return True
    return False

def batch(directory):
    '''
    Batch processes every book in the speciified directory.
    '''
    # create a bounded semaphore to manage the work threads
    thread_pool = BoundedSemaphore(value=_MAX_THREADS)
    # loop through the files
    for filename in pg_funcs.get_files(directory):
        # check if the book already exists, if so skip to the next one
        if does_book_exist(pg_funcs.extract_bookid(filename)):
            print('Book:', filename, 'already exists, it will not be added to the database!')
            continue
        # skip stuff that shouldnt be indexed
        if ('readme' in filename or 
                'index' in filename or 
                'body' in filename or
                'mac' in filename):
            continue
        # indexing utf files causes certain books to get indexed twice, skip them
        if ('-0.txt' in filename or 
                'utf8' in filename or 
                'utf16' in filename):
            continue
        # the bounded semaphore handles controlling the thread for us
        with thread_pool:
            EBookParser.thread_count += 1
            t = EBookParser(filename)
            t.start()
            if EBookParser.thread_count == _MAX_THREADS:
                t.join()

def single(filepath):
    '''
    Parses a single ebook and adds it to the database.
    '''
    # check if the book already exists, if so skip to the next one
    if does_book_exist(pg_funcs.extract_bookid(filepath)):
        print('Book:', filepath, 'already exists, it will not be added to the database!')
        return
    t = EBookParser(filepath)
    t.start()
    t.join()
    client.insert_one(t.book)
    # write the stem file to disk
    write_stem_file(os.path.join(stempath, t.book['bookid']+'.txt'), t.stems)

'''
Main method, called when the program executes.
'''
def main():
    if len(sys.argv) != 2:
        print('Error: Invalid number of arguments presented!')
        print_help()
        sys.exit(-1)
    if sys.argv[1] == '-h' or sys.argv[1] == '--help':
        print_help()
        sys.exit(0)
    # create the stems output directory if needed
    if not os.path.exists(stempath):
        os.mkdir(os.path.join(stempath))
    # get the directory/file
    arg = sys.argv[1]
    if os.path.isdir(arg):
        batch(arg)
    # otherwise parse a single file
    elif os.path.isfile(arg) and arg.endswith('.txt'):
        single(arg)
    client.close()

if __name__ == '__main__':
    main()
