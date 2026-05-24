db.createCollection("reviews")

db.reviews.insertOne({

  order_id: "order_001",

  product_id: "product_001",

  customer_id: "customer_001",

  review_score: 5,

  title: "Excelente producto",

  message: "Muy buena calidad y entrega rápida.",

  sentiment: {
    label: "positive",
    score: 0.94
  },

  tags: [
    "fast-delivery",
    "high-quality"
  ],

  created_at: new Date()
})