# guttenberg-search
Guttenberg Project search engine built using simple tf.idf and vector ranking techniques

## tf.idf background
tf.idf or (T)erm (F)requency * (I)nverted (D)ocument (F)requency is a fundamental information retrieval technique. It attempts to balance the issues that arise from relating queries to documents by utilizng the term frequency via weighting with document frequency. Inverted document frequency is used to ensure that the rarest search terms that appear in a query over a collection of documents have higher weight then more common search terms (as documents containing rarer words are considered to be more relevant to the search query than documents containing less rare words. This is similar to the techniques employed for the very early version of the Google search engine (which since, has become vastly more complicated).

Rarity of a word is defined using: 
- The term frequency: the amount of times a term appears in a single document
- The document frequency: the amount of documents a term appears in at least once (cannot be greater than N, the size of the document collection)
- The collection frequency: the total amount of times the term appears across all documents in the collection

## Vector ranking background
Vector ranking is a query/document scoring mechanism that utilizes a so-called [cosine similarity](https://en.wikipedia.org/wiki/Cosine_similarity) index to compute the angle of intersection between the query plane and the document plane. The closer the angle is to zero, the more relevant the document is to the query and the higher its overall ranking in the returned results to the user. A fully orthoganal cosine similiarity index indicates that the document is not relevant at all to the query and should not be returned in the result set.

