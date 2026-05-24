db.createCollection("products")

db.products.insertOne({

  name: "Mechanical Gaming Keyboard",

  category: {
    original: "informatica_acessorios",
    english: "computers_accessories"
  },

  attributes: {
    switch_type: "blue",
    rgb: true,
    wireless: false
  },

  dimensions: {
    weight_g: 1200,
    length_cm: 45,
    height_cm: 5,
    width_cm: 15
  },

  media: [
    {
      type: "image",
      url: "https://cdn.ecommify.com/kb.png"
    }
  ],

  ratings: {
    average: 4.8,
    count: 2540
  },

  tags: [
    "gaming",
    "rgb",
    "mechanical"
  ],

  created_at: new Date()
})