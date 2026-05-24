db.reviews.aggregate([

  {
    $group: {
      _id: "$product_id",
      average_rating: {
        $avg: "$review_score"
      },
      total_reviews: {
        $sum: 1
      }
    }
  },

  {
    $sort: {
      average_rating: -1
    }
  }
])