db.createCollection("carts")

db.carts.insertOne({

  customer_id: "customer_001",

  items: [
    {
      product_id: "product_001",
      quantity: 2,
      price_snapshot: 120
    }
  ],

  subtotal: 240,

  expires_at: new Date(
    Date.now() + 1000 * 60 * 60 * 24
  ),

  updated_at: new Date()
})