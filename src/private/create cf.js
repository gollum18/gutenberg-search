// This guy creates the collection frequency (cf)
//   In this context, the cf is how many documents a term appears in
db.doc_freqs.aggregate([
    // convert the terms object to an array for the next stage
    { $project: { terms: { $objectToArray: "$terms" } } },
    // unwind the array from the last stage so we get a document 
    //  for each k/v pair from the array
    { $unwind: "$terms" },
    // group on the term adding 1 for each appearance of the term
    //  important! this gets the collection frequency
    { $group: { 
            _id: "$terms.k",
            count: { $sum: 1 }
        } 
    }, 
    // sort ascending by term
    { $sort: { _id: 1 } },
    // output the collection frequency collection
    { $out: "coll_freqs" } 
], { "allowDiskUse": true } )