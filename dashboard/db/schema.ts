import { sqliteTable, text, integer, index, primaryKey } from "drizzle-orm/sqlite-core";
export const reviews = sqliteTable("reviews", {
  datasetId:text("dataset_id").notNull(),reviewId:text("review_id").notNull(), sourceHash:text("source_hash").notNull(),
  sourceJson:text("source_json").notNull(), predictionJson:text("prediction_json"),
  status:text("status").notNull(), topic:text("topic"), intent:text("intent"),
  severity:integer("severity"), needsReview:integer("needs_review")
},table=>[primaryKey({columns:[table.datasetId,table.reviewId]}),index("idx_reviews_dataset_topic_intent").on(table.datasetId,table.topic,table.intent)]);
export const analysis = sqliteTable("analysis", {key:text("key").primaryKey(),value:text("value").notNull()});
