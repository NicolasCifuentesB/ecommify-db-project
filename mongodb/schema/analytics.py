db.createCollection("analytics_orders")

db.analytics_orders.insertOne({

  order_id: "order_001",

  customer: {
    city: "Sao Paulo",
    state: "SP"
  },

  products: [
    {
      product_id: "product_001",
      category: "electronics",
      price: 599.99
    }
  ],

  payments: {
    type: "credit_card",
    installments: 3
  },

  review_score: 5,

  purchase_timestamp: new Date()
})