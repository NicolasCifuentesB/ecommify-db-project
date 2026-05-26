db.createCollection("recommendations")

db.recommendations.insertOne({

  customer_id: "customer_001",

  recommended_products: [
    {
      product_id: "product_042",
      score: 0.97,
      reason: "collaborative_filtering"
    },
    {
      product_id: "product_015",
      score: 0.91,
      reason: "content_based"
    }
  ],

  context: {
    last_category_viewed: "computers_accessories",
    last_order_id: "order_001"
  },

  generated_at: new Date(),

  expires_at: new Date(Date.now() + 1000 * 60 * 60 * 24 * 7)
})

db.recommendations.createIndex(
  { expires_at: 1 },
  { expireAfterSeconds: 0 }
)

db.recommendations.createIndex({ customer_id: 1 })

db.recommendations.createIndex({ "recommended_products.score": -1 })
