/* This aggregate function executes a tf-idf query over the entire books collection.
 */
db.books.aggregate([ 
    // this stage gets the document frequency
    { $lookup: {
            from: "doc_freqs",
            localField: "bookid",
            foreignField: "bookid",
            as: "joined_terms"
        }
    },
    // this stage converts the document frequency to a format we can work with
    { $project: { bookid: "$bookid", "book_terms": { $arrayElemAt: [ "$joined_terms.terms", 0 ] } } },
    { $project: { bookid: "$bookid", "book_terms": { $objectToArray: "$book_terms" } } },
    // this stage gets the collection frequency, this is the bottleneck stage
    // there has to be a way to optimize it
    { $lookup: {
            from: "coll_freqs",
            localField: "book_terms.k",
            foreignField: "_id",
            as: "tfd_index"
        }
    },
    // this stage replaces each document with an array of terms, an array of document freqs, and an array of collection freqs
    { $replaceRoot: { newRoot: { bookid: "$bookid", terms: "$book_terms.k", dfs: "$book_terms.v", cfs: "$tfd_index.value" } } },
    // zips all three arrays above into a single array containing arrays with three elements
    { $project: { bookid: "$bookid", index: { $zip: {inputs: ["$terms", "$dfs", "$cfs"] } } } },
    // perform the tf.idf on the array above
    // TODO: The bookid needs passed along all the way here
    { $project: 
        { bookid: "$bookid", 
          tfidf: 
            { $map: 
                {
                    input: "$index",
                    as: "tfidf",
                    in: { $multiply:
                            [ 
                                // this term is the tf
                                { $log10: { 
                                    $add: [
                                        1, 
                                        { $arrayElemAt: [ "$$tfidf", 1 ] } 
                                    ] } 
                                },
                                // this term is the idf
                                { $log10: { 
                                    $divide: [
                                        // hard coded number of documents, best I can do for now
                                        // TODO: it should really be passed all the way to this stage too, like bookid
                                        9285, 
                                        { $add: [ 1, { $arrayElemAt: [ "$$tfidf", 2 ] } ] } 
                                    ] } 
                                }
                            ] 
                        }
                }   
            }
        } 
    }
])