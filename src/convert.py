import pymongo
import os
import snowballstemmer
import string
import sys

from io import StringIO
from threading import Thread

class EBookParser(Thread):

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
    Creates a new EBookParser thread that parses the ebook stored 
    at the specified filename.
        filename: The address of the book on disk.
    '''
    def __init__(self, filename):
        Thread.__init__(self)
        self.filename = filename
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
                f = open(self.filename)
                raw_data = f.read()
            except UnicodeDecodeError:
                try:
                    f = open(self.filename, encoding='ascii')
                    raw_data = f.read()
                except UnicodeDecodeError:
                    try:
                        f = open(self.filename, encoding='iso-8859-1')
                        raw_data = f.read()
                    except UnicodeDecodeError:
                        print('Unknown encoding for:', self.filename)
                        return
                    finally:
                        f.close()
                finally:
                    f.close()
            finally:
                f.close()
            for line in StringIO(raw_data):
                print(line)
        except IOError:
            print('An IOError occured processing file:', self.filename)


'''
Generator function for lazily stepping through the ebook files.
    root: the root directory that the ebook text files are stored in.
'''
def get_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        for filename in filenames:
            if filename.endswith('.txt'):
                yield dirpath + os.sep + filename

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
    for f in get_files(sys.argv[1]):
        t = EBookParser(f)
        t.start()
        t.join()
        stems = ' '.join(t.stems)

if __name__ == '__main__':
    main()
