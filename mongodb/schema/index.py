db.carts.createIndex(
  { expires_at: 1 },
  { expireAfterSeconds: 0 }
)

db.products.createIndex({
  tags: 1
})

db.reviews.createIndex({
  review_score: -1
})

db.products.createIndex({
  "ratings.average": -1
})

db.products.createIndex({
  "category.english": 1
})