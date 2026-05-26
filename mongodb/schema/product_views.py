db.createCollection("product_views")

db.product_views.insertOne({

  customer_id: "customer_001",

  product_id: "product_042",

  category: "computers_accessories",

  session_id: "sess_abc123",

  duration_seconds: 45,

  source: "search",

  viewed_at: new Date()
})

db.product_views.createIndex({ customer_id: 1 })

db.product_views.createIndex({ product_id: 1 })

db.product_views.createIndex({ viewed_at: -1 })

db.product_views.createIndex(
  { viewed_at: 1 },
  { expireAfterSeconds: 60 * 60 * 24 * 90 }
)
