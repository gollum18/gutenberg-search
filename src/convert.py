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
        'Release Date: ': 'release_date',
        'Posting Date: ': 'posting_date',
        'Language: ': 'language',
        'Character set encoding: ': 'char_set',
        'Chatacter set encoding: ': 'char_set',
        'Produced by ': 'publisher'
    }

    def __init__(self, filename):
        Thread.__init__(self)
        self.filename = filename
        self.book = dict()
        self.stems = []

    def run(self):
        # try to open the file in utf-8, ascii, or iso-8895-1
        #   if theres an error, print out the filename
        # this is ugly and not the best solution, but the best I can think
        #   of right now to deal with the varying encodings
        # not sure if the three finallys are necessary or if I could 
        #   use just one, but its fine
        try:
            data = None
            try:
                f = open(self.filename)
                data = f.read()
            except UnicodeDecodeError:
                try:
                    f = open(self.filename, encoding='ascii')
                    data = f.read()
                except UnicodeDecodeError:
                    try:
                        f = open(self.filename, encoding='iso-8859-1')
                        data = f.read()
                    except UnicodeDecodeError:
                        print('Unknown encoding for:', self.filename)
                        return
                    finally:
                        f.close()
                finally:
                    f.close()
            finally:
                f.close()
        except IOError:
            print('An IOError occured processing file:', filename)

'''
Generator function for lazily stepping through the ebook files.
'''
def get_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        for filename in filenames:
            if filename.endswith('.txt'):
                yield dirpath + os.sep + filename

'''
Main method, called when the program executes.
'''
def main(root):
    for f in get_files(root):
        t = EBookParser(f)
        t.start()
        t.join()
        stems = ' '.join(t.stems)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('usage python3 convert.py [root directory]')
        sys.exit(5)
    main(sys.argv[1])
