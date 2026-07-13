import { and, eq } from "drizzle-orm";
import { drizzle } from "drizzle-orm/mysql2";
import { InsertUser, users, Tool, InsertTool, UpdateTool, tools, toolLogs } from "../drizzle/schema";
import { ENV } from './_core/env';

let _db: ReturnType<typeof drizzle> | null = null;

// Lazily create the drizzle instance so local tooling can run without a DB.
export async function getDb() {
  if (!_db && process.env.DATABASE_URL) {
    try {
      _db = drizzle(process.env.DATABASE_URL);
    } catch (error) {
      console.warn("[Database] Failed to connect:", error);
      _db = null;
    }
  }
  return _db;
}

export async function upsertUser(user: InsertUser): Promise<void> {
  if (!user.openId) {
    throw new Error("User openId is required for upsert");
  }

  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot upsert user: database not available");
    return;
  }

  try {
    const values: InsertUser = {
      openId: user.openId,
    };
    const updateSet: Record<string, unknown> = {};

    const textFields = ["name", "email", "loginMethod"] as const;
    type TextField = (typeof textFields)[number];

    const assignNullable = (field: TextField) => {
      const value = user[field];
      if (value === undefined) return;
      const normalized = value ?? null;
      values[field] = normalized;
      updateSet[field] = normalized;
    };

    textFields.forEach(assignNullable);

    if (user.lastSignedIn !== undefined) {
      values.lastSignedIn = user.lastSignedIn;
      updateSet.lastSignedIn = user.lastSignedIn;
    }
    if (user.role !== undefined) {
      values.role = user.role;
      updateSet.role = user.role;
    } else if (user.openId === ENV.ownerOpenId) {
      values.role = 'admin';
      updateSet.role = 'admin';
    }

    if (!values.lastSignedIn) {
      values.lastSignedIn = new Date();
    }

    if (Object.keys(updateSet).length === 0) {
      updateSet.lastSignedIn = new Date();
    }

    await db.insert(users).values(values).onDuplicateKeyUpdate({
      set: updateSet,
    });
  } catch (error) {
    console.error("[Database] Failed to upsert user:", error);
    throw error;
  }
}

export async function getUserByOpenId(openId: string) {
  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot get user: database not available");
    return undefined;
  }

  const result = await db.select().from(users).where(eq(users.openId, openId)).limit(1);

  return result.length > 0 ? result[0] : undefined;
}

/**
 * Tools Management Queries
 */
export async function createTool(userId: number, toolData: InsertTool) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  
  const result = await db.insert(tools).values({
    ...toolData,
    userId,
  });
  return result;
}

export async function getUserTools(userId: number) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  
  return db.select().from(tools).where(eq(tools.userId, userId));
}

export async function getToolByKey(key: string) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  
  const result = await db.select().from(tools).where(eq(tools.key, key)).limit(1);
  return result.length > 0 ? result[0] : null;
}

export async function updateTool(key: string, updates: Partial<InsertTool>) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  
  return db.update(tools).set(updates).where(eq(tools.key, key));
}

export async function updateToolMetadata(key: string, name: string, description?: string) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  
  const updates: Record<string, unknown> = { name };
  if (description !== undefined) {
    updates.description = description || null;
  }
  
  return db.update(tools).set(updates).where(eq(tools.key, key));
}

export async function deleteTool(key: string) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  
  return db.delete(tools).where(eq(tools.key, key));
}

export async function addToolLog(toolId: number, sessionId: string, message: string, type: 'log' | 'success' | 'error' | 'warning' | 'status' = 'log') {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  
  return db.insert(toolLogs).values({
    toolId,
    sessionId,
    message,
    type,
  });
}

export async function getToolLogs(toolId: number, sessionId: string) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  
  return db.select().from(toolLogs).where(
    and(eq(toolLogs.toolId, toolId), eq(toolLogs.sessionId, sessionId))
  );
}
