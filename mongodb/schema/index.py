db.carts.createIndex(
  { expires_at: 1 },
  { expireAfterSeconds: 0 }
)

db.products.createIndex({ tags: 1 })

db.products.createIndex({ "ratings.average": -1 })

db.products.createIndex({ "category.english": 1 })

// reviews: índices para las tres referencias cruzadas
db.reviews.createIndex({ review_score: -1 })

db.reviews.createIndex({ customer_id: 1 })

db.reviews.createIndex({ order_id: 1 })

db.reviews.createIndex({ product_id: 1 })

// analytics_orders: índice por order_id para joins cruzados PG → Mongo
db.analytics_orders.createIndex({ order_id: 1 })