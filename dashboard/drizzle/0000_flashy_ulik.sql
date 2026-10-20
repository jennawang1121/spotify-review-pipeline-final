CREATE TABLE `analysis` (
	`key` text PRIMARY KEY NOT NULL,
	`value` text NOT NULL
);
--> statement-breakpoint
CREATE TABLE `reviews` (
	`dataset_id` text NOT NULL,
	`review_id` text NOT NULL,
	`source_hash` text NOT NULL,
	`source_json` text NOT NULL,
	`prediction_json` text,
	`status` text NOT NULL,
	`topic` text,
	`intent` text,
	`severity` integer,
	`needs_review` integer,
	PRIMARY KEY(`dataset_id`, `review_id`)
);
--> statement-breakpoint
CREATE INDEX `idx_reviews_dataset_topic_intent` ON `reviews` (`dataset_id`,`topic`,`intent`);