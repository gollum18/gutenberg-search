# gutenberg-search
Gutenberg Project search engine built using a multi-phase inverted index, tf.idf, and vector ranking to retrieve relevant books to their search query. This should be wrapped in a nice web front-end (probably in Node.js with Express/Pug), that functions similarly to Google or Bing, although since I despise CSS, it won't look as pretty.

How many eBooks are we talking here? Outside of becoming a mirror, which I did not want to do, there are not that many other ways to pull down files from the Gutenberg Project. I ended up using the wget method listed on the projects website to pull down exactly 22,760 English eBooks. I would have gathered more, but I had no way to prevent the wget script from pulling down different encodings of the same eBook (which led to an an original collection size of roughly ~57,000 books). If you want to replicate the collection, please use the `convert.py` script to do so (after you have pulled down the books you want). It is currently setup to (painfully) convert the eBooks to a suitable format for a MongoDB database (currently pointed to at localhost, although that's very wasy to change). 

The script currently only runs on GNU Linux machines that have the `strings` program available. This is a comprimise I made after having to deal with the library having multiple different character encodings, eeven though each book is supposeed to be just plain old ASCII. This slows down the program a lot, but prevents me from having to deal with the encoding issue directly.

## inverted index?
todo: explain what an inverted index is.

## tf.idf?
tf.idf or (T)erm (F)requency * (I)nverted (D)ocument (F)requency is a fundamental information retrieval technique. It attempts to balance the issues that arise from relating queries to documents by utilizng the term frequency via weighting with document frequency. Inverted document frequency is used to ensure that the rarest search terms that appear in a query over a collection of documents have higher weight then more common search terms (as documents containing rarer words are considered to be more relevant to the search query than documents containing less rare words. This is similar to the techniques employed for the very early version of the Google search engine (which since, has become vastly more complicated).

Rarity of a word is defined using: 
- The term frequency: the amount of times a term appears in a single document
- The document frequency: the amount of documents a term appears in at least once (cannot be greater than N, the size of the document collection)
- The collection frequency: the total amount of times the term appears across all documents in the collection

## vector ranking?
Vector ranking is a query/document scoring mechanism that utilizes a so-called [cosine similarity](https://en.wikipedia.org/wiki/Cosine_similarity) index to compute the angle of intersection between the query plane and the document plane. The closer the angle is to zero, the more relevant the document is to the query and the higher its overall ranking in the returned results to the user. A fully orthoganal cosine similiarity index indicates that the document is not relevant at all to the query and should not be returned in the result set. It's nice, I'm actually using something I learned in Calculus for a real world application.

## can I contribute?
Not yet! Any contributions will have to wait until this status is updated. This is a term project for CIS 612: Big Data and Parallel Database Systems and I am required to build it by myself. I would gladly accept any assistance once I submit it though.
