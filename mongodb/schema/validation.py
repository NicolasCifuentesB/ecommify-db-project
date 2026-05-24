db.runCommand({

  collMod: "reviews",

  validator: {

    $jsonSchema: {

      bsonType: "object",

      required: [
        "order_id",
        "product_id",
        "review_score"
      ],

      properties: {

        review_score: {
          bsonType: "int",
          minimum: 1,
          maximum: 5
        }
      }
    }
  }
})