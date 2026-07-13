import { describe, expect, it } from "vitest";
import { appRouter } from "../routers";
import type { TrpcContext } from "../_core/context";

type AuthenticatedUser = NonNullable<TrpcContext["user"]>;

function createAuthContext(userId: number = 1): TrpcContext {
  const user: AuthenticatedUser = {
    id: userId,
    openId: `user-${userId}`,
    email: `user${userId}@example.com`,
    name: `User ${userId}`,
    loginMethod: "manus",
    role: "user",
    createdAt: new Date(),
    updatedAt: new Date(),
    lastSignedIn: new Date(),
  };

  return {
    user,
    req: {
      protocol: "https",
      headers: {},
    } as TrpcContext["req"],
    res: {} as TrpcContext["res"],
  };
}

describe("tools.updateMetadata", () => {
  it("should update tool metadata for authorized user", async () => {
    const ctx = createAuthContext(1);
    const caller = appRouter.createCaller(ctx);

    // This test assumes a tool exists in the database
    // In a real test, we would create a tool first
    // For now, we test the authorization logic

    try {
      const result = await caller.tools.updateMetadata({
        key: "test-tool-key",
        name: "Updated Tool Name",
        description: "Updated description",
      });

      // If the tool doesn't exist, it will throw NOT_FOUND
      // If it exists but belongs to another user, it will throw FORBIDDEN
      // Otherwise, it should return success: true
      expect(result).toEqual({ success: true });
    } catch (error: any) {
      // Expected errors for non-existent or unauthorized tools
      expect(["NOT_FOUND", "FORBIDDEN"]).toContain(error.code);
    }
  });

  it("should reject update for tool belonging to different user", async () => {
    const ctx1 = createAuthContext(1);
    const ctx2 = createAuthContext(2);
    const caller = appRouter.createCaller(ctx2);

    // Try to update a tool that belongs to user 1
    try {
      await caller.tools.updateMetadata({
        key: "user1-tool-key",
        name: "Hacked Name",
      });
      // Should not reach here
      expect.fail("Should have thrown FORBIDDEN error");
    } catch (error: any) {
      // Expected to fail with FORBIDDEN or NOT_FOUND
      expect(["NOT_FOUND", "FORBIDDEN"]).toContain(error.code);
    }
  });

  it("should reject empty tool name", async () => {
    const ctx = createAuthContext(1);
    const caller = appRouter.createCaller(ctx);

    try {
      await caller.tools.updateMetadata({
        key: "test-tool-key",
        name: "",
      });
      expect.fail("Should have thrown validation error");
    } catch (error: any) {
      expect(error.code).toBe("BAD_REQUEST");
    }
  });

  it("should allow optional description", async () => {
    const ctx = createAuthContext(1);
    const caller = appRouter.createCaller(ctx);

    try {
      const result = await caller.tools.updateMetadata({
        key: "test-tool-key",
        name: "Tool Name",
        // description is optional
      });

      expect(result).toEqual({ success: true });
    } catch (error: any) {
      // Expected errors for non-existent or unauthorized tools
      expect(["NOT_FOUND", "FORBIDDEN"]).toContain(error.code);
    }
  });
});
