import { int, mysqlEnum, mysqlTable, text, timestamp, varchar } from "drizzle-orm/mysql-core";

/**
 * Core user table backing auth flow.
 * Extend this file with additional tables as your product grows.
 * Columns use camelCase to match both database fields and generated types.
 */
export const users = mysqlTable("users", {
  /**
   * Surrogate primary key. Auto-incremented numeric value managed by the database.
   * Use this for relations between tables.
   */
  id: int("id").autoincrement().primaryKey(),
  /** Manus OAuth identifier (openId) returned from the OAuth callback. Unique per user. */
  openId: varchar("openId", { length: 64 }).notNull().unique(),
  name: text("name"),
  email: varchar("email", { length: 320 }),
  loginMethod: varchar("loginMethod", { length: 64 }),
  role: mysqlEnum("role", ["user", "admin"]).default("user").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
  lastSignedIn: timestamp("lastSignedIn").defaultNow().notNull(),
});

export type User = typeof users.$inferSelect;
export type InsertUser = typeof users.$inferInsert;

/**
 * Tools registry table for managing registered Python tools
 */
export const tools = mysqlTable("tools", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull(),
  key: varchar("key", { length: 255 }).notNull().unique(),
  name: varchar("name", { length: 255 }).notNull(),
  description: text("description"),
  src: text("src").notNull(),
  toolDir: text("toolDir").notNull(),
  rootDir: text("rootDir").notNull(),
  entrypoint: text("entrypoint"),
  lastInstallBackend: varchar("lastInstallBackend", { length: 64 }),
  lastInstallSuccess: int("lastInstallSuccess"),
  lastInstallOutput: text("lastInstallOutput"),
  lastSmokeTestReturnCode: int("lastSmokeTestReturnCode"),
  lastSmokeTestOutput: text("lastSmokeTestOutput"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type Tool = typeof tools.$inferSelect;
export type InsertTool = typeof tools.$inferInsert;
export type UpdateTool = Partial<Omit<Tool, 'id' | 'userId' | 'key' | 'createdAt'>>;

/**
 * Tool execution logs for streaming output
 */
export const toolLogs = mysqlTable("toolLogs", {
  id: int("id").autoincrement().primaryKey(),
  toolId: int("toolId").notNull(),
  sessionId: varchar("sessionId", { length: 64 }).notNull(),
  timestamp: timestamp("timestamp").defaultNow().notNull(),
  message: text("message").notNull(),
  type: mysqlEnum("type", ["log", "success", "error", "warning", "status"]).default("log").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
});

export type ToolLog = typeof toolLogs.$inferSelect;
export type InsertToolLog = typeof toolLogs.$inferInsert;