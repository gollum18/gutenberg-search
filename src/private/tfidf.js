/* This aggregate function executes a tf-idf query over the entire books collection.
 */
db.books.aggregate([
    // this stage gets the document frequency
    { $lookup: 
        {
            from: "doc_freqs",
            localField: "bookid",
            foreignField: "bookid",
            as: "joined_terms"
        }
    },
    // this stage converts the document frequency to a format we can work with
    { $project: 
        { 
            bookid: "$bookid", 
            filepath: "$filepath",
            book_terms: { 
                $filter: {
                    input: { $objectToArray: { $arrayElemAt: [ "$joined_terms.terms", 0 ] } },
                    as: "term_freq",
                    cond: { $in: ["$$term_freq.k", ['a', 'aa', 'aaa'] ] }
                }
            }
        } 
    },
    // I shouldnt have had to do this, but I'm relatively certain this is the only 
    //  way I can in MongoDB, have to reproject the stuff above with the same values
    //  plus a count of the book terms
    { $project: 
        { 
            bookid: "$bookid", 
            filepath: "$filepath",
            book_terms: "$book_terms",
            count: { $size: "$book_terms" }
        } 
    },
    // filter out the documents that do not have any matching book terms
    { $match: 
        {
            count: {$gt: 0}
        } 
    },
    // this stage joins the collection frequency to the doc frequency
    { $lookup: 
        {
            from: "coll_freqs",
            localField: "book_terms.k",
            foreignField: "_id",
            as: "tfd_index"
        }
    },
    // this stage replaces each document with an array of terms, an array of document freqs, and an array of collection freqs
    { $replaceRoot: 
        { newRoot: 
            { 
                bookid: "$bookid", 
                filepath: "$filepath", 
                terms: "$book_terms.k", dfs: "$book_terms.v", cfs: "$tfd_index.count" 
            } 
        } 
    },
    // zips all three arrays above into a single array containing arrays with three elements
    { $project: { 
            bookid: "$bookid", 
            filepath: "$filepath", 
            index: { $zip: {inputs: ["$terms", "$dfs", "$cfs"] } } 
        } 
    },
    // perform the tf.idf on the array above
    // TODO: The bookid needs passed along all the way here
    { $project: 
        { bookid: "$bookid", 
          filepath: "$filepath",
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