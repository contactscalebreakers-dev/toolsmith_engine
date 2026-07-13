CREATE TABLE `toolLogs` (
	`id` int AUTO_INCREMENT NOT NULL,
	`toolId` int NOT NULL,
	`sessionId` varchar(64) NOT NULL,
	`timestamp` timestamp NOT NULL DEFAULT (now()),
	`message` text NOT NULL,
	`type` enum('log','success','error','warning','status') NOT NULL DEFAULT 'log',
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `toolLogs_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `tools` (
	`id` int AUTO_INCREMENT NOT NULL,
	`userId` int NOT NULL,
	`key` varchar(255) NOT NULL,
	`name` varchar(255) NOT NULL,
	`src` text NOT NULL,
	`toolDir` text NOT NULL,
	`rootDir` text NOT NULL,
	`entrypoint` text,
	`lastInstallBackend` varchar(64),
	`lastInstallSuccess` int,
	`lastInstallOutput` text,
	`lastSmokeTestReturnCode` int,
	`lastSmokeTestOutput` text,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `tools_id` PRIMARY KEY(`id`),
	CONSTRAINT `tools_key_unique` UNIQUE(`key`)
);
