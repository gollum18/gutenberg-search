import os

'''
Extracts the bookid from a given filepath.
'''
def extract_bookid(filepath):
    parts = filepath.split(os.path.sep)
    bookid = parts[len(parts)-1].replace('.txt', '')
    return bookid

'''
Generator function for lazily stepping through files in a .
    root: the root directory to index files from.
'''
def get_files(root, ext='.txt'):
    for dirpath, dirnames, filenames in os.walk(root):
        for filename in filenames:
            if filename.endswith(ext):
                yield dirpath + os.sep + filename
