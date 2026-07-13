import { describe, expect, it, vi, beforeEach } from "vitest";
import { toolsRouter } from "./tools";
import * as db from "../db";
import { TRPCError } from "@trpc/server";

// Mock the database module
vi.mock("../db", () => ({
  createTool: vi.fn(),
  getUserTools: vi.fn(),
  getToolByKey: vi.fn(),
  updateTool: vi.fn(),
  deleteTool: vi.fn(),
  addToolLog: vi.fn(),
  getToolLogs: vi.fn(),
}));

// Mock context
const mockContext = {
  user: {
    id: 1,
    openId: "test-user",
    name: "Test User",
    email: "test@example.com",
    role: "user" as const,
    createdAt: new Date(),
    updatedAt: new Date(),
    lastSignedIn: new Date(),
  },
};

describe("Tools Router", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("list", () => {
    it("should return user's tools", async () => {
      const mockTools = [
        {
          id: 1,
          userId: 1,
          key: "test-tool-1",
          name: "Test Tool 1",
          src: "/path/to/tool1",
          toolDir: "/tools/tool1",
          rootDir: "/tools/tool1/src",
          entrypoint: "main.py",
          lastInstallBackend: "pip",
          lastInstallSuccess: 1,
          lastInstallOutput: "Success",
          lastSmokeTestReturnCode: 0,
          lastSmokeTestOutput: "Pass",
          createdAt: new Date(),
          updatedAt: new Date(),
        },
      ];

      vi.mocked(db.getUserTools).mockResolvedValue(mockTools as any);

      const caller = toolsRouter.createCaller(mockContext);
      const result = await caller.list();

      expect(result).toEqual(mockTools);
      expect(db.getUserTools).toHaveBeenCalledWith(1);
    });
  });

  describe("register", () => {
    it("should register a new tool", async () => {
      vi.mocked(db.getToolByKey).mockResolvedValue(null);
      vi.mocked(db.createTool).mockResolvedValue({ insertId: 1 } as any);

      const caller = toolsRouter.createCaller(mockContext);
      const result = await caller.register({
        key: "new-tool",
        name: "New Tool",
        src: "/path/to/tool",
        toolDir: "/tools/new-tool",
        rootDir: "/tools/new-tool/src",
        entrypoint: "main.py",
      });

      expect(result).toBeDefined();
      expect(db.createTool).toHaveBeenCalledWith(1, expect.objectContaining({
        key: "new-tool",
        name: "New Tool",
      }));
    });

    it("should reject if tool key already exists", async () => {
      vi.mocked(db.getToolByKey).mockResolvedValue({
        id: 1,
        userId: 1,
        key: "existing-tool",
        name: "Existing Tool",
      } as any);

      const caller = toolsRouter.createCaller(mockContext);

      await expect(
        caller.register({
          key: "existing-tool",
          name: "New Tool",
          src: "/path/to/tool",
          toolDir: "/tools/tool",
          rootDir: "/tools/tool/src",
        })
      ).rejects.toThrow("Tool with this key already exists");
    });
  });

  describe("get", () => {
    it("should return tool details for authorized user", async () => {
      const mockTool = {
        id: 1,
        userId: 1,
        key: "test-tool",
        name: "Test Tool",
        src: "/path/to/tool",
        toolDir: "/tools/tool",
        rootDir: "/tools/tool/src",
        entrypoint: "main.py",
        lastInstallBackend: "pip",
        lastInstallSuccess: 1,
        lastInstallOutput: "Success",
        lastSmokeTestReturnCode: 0,
        lastSmokeTestOutput: "Pass",
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      vi.mocked(db.getToolByKey).mockResolvedValue(mockTool as any);

      const caller = toolsRouter.createCaller(mockContext);
      const result = await caller.get({ key: "test-tool" });

      expect(result).toEqual(mockTool);
    });

    it("should reject if tool not found", async () => {
      vi.mocked(db.getToolByKey).mockResolvedValue(null);

      const caller = toolsRouter.createCaller(mockContext);

      await expect(
        caller.get({ key: "nonexistent-tool" })
      ).rejects.toThrow("Tool not found");
    });

    it("should reject if user is not tool owner", async () => {
      const mockTool = {
        id: 1,
        userId: 999, // Different user
        key: "test-tool",
        name: "Test Tool",
      };

      vi.mocked(db.getToolByKey).mockResolvedValue(mockTool as any);

      const caller = toolsRouter.createCaller(mockContext);

      await expect(
        caller.get({ key: "test-tool" })
      ).rejects.toThrow("You do not have access to this tool");
    });
  });

  describe("remove", () => {
    it("should remove a tool for authorized user", async () => {
      const mockTool = {
        id: 1,
        userId: 1,
        key: "test-tool",
        name: "Test Tool",
      };

      vi.mocked(db.getToolByKey).mockResolvedValue(mockTool as any);
      vi.mocked(db.deleteTool).mockResolvedValue({} as any);

      const caller = toolsRouter.createCaller(mockContext);
      const result = await caller.remove({ key: "test-tool" });

      expect(result).toEqual({ success: true });
      expect(db.deleteTool).toHaveBeenCalledWith("test-tool");
    });

    it("should reject if tool not found", async () => {
      vi.mocked(db.getToolByKey).mockResolvedValue(null);

      const caller = toolsRouter.createCaller(mockContext);

      await expect(
        caller.remove({ key: "nonexistent-tool" })
      ).rejects.toThrow("Tool not found");
    });

    it("should reject if user is not tool owner", async () => {
      const mockTool = {
        id: 1,
        userId: 999,
        key: "test-tool",
      };

      vi.mocked(db.getToolByKey).mockResolvedValue(mockTool as any);

      const caller = toolsRouter.createCaller(mockContext);

      await expect(
        caller.remove({ key: "test-tool" })
      ).rejects.toThrow("You do not have access to this tool");
    });
  });

  describe("updateInstallStatus", () => {
    it("should update install status for authorized user", async () => {
      const mockTool = {
        id: 1,
        userId: 1,
        key: "test-tool",
      };

      vi.mocked(db.getToolByKey).mockResolvedValue(mockTool as any);
      vi.mocked(db.updateTool).mockResolvedValue({} as any);

      const caller = toolsRouter.createCaller(mockContext);
      const result = await caller.updateInstallStatus({
        key: "test-tool",
        backend: "pip",
        success: true,
        output: "Installation successful",
      });

      expect(result).toEqual({ success: true });
      expect(db.updateTool).toHaveBeenCalledWith("test-tool", expect.objectContaining({
        lastInstallBackend: "pip",
        lastInstallSuccess: 1,
      }));
    });

    it("should reject if user is not tool owner", async () => {
      const mockTool = {
        id: 1,
        userId: 999,
        key: "test-tool",
      };

      vi.mocked(db.getToolByKey).mockResolvedValue(mockTool as any);

      const caller = toolsRouter.createCaller(mockContext);

      await expect(
        caller.updateInstallStatus({
          key: "test-tool",
          backend: "pip",
          success: true,
        })
      ).rejects.toThrow("You do not have access to this tool");
    });
  });

  describe("updateSmokeTestStatus", () => {
    it("should update smoke test status for authorized user", async () => {
      const mockTool = {
        id: 1,
        userId: 1,
        key: "test-tool",
      };

      vi.mocked(db.getToolByKey).mockResolvedValue(mockTool as any);
      vi.mocked(db.updateTool).mockResolvedValue({} as any);

      const caller = toolsRouter.createCaller(mockContext);
      const result = await caller.updateSmokeTestStatus({
        key: "test-tool",
        returnCode: 0,
        output: "Test passed",
      });

      expect(result).toEqual({ success: true });
      expect(db.updateTool).toHaveBeenCalledWith("test-tool", expect.objectContaining({
        lastSmokeTestReturnCode: 0,
      }));
    });
  });

  describe("addLog", () => {
    it("should add a log entry for authorized user", async () => {
      const mockTools = [
        { id: 1, userId: 1, key: "test-tool" },
      ];

      vi.mocked(db.getUserTools).mockResolvedValue(mockTools as any);
      vi.mocked(db.addToolLog).mockResolvedValue({} as any);

      const caller = toolsRouter.createCaller(mockContext);
      const result = await caller.addLog({
        toolId: 1,
        sessionId: "session-123",
        message: "Tool started",
        type: "status",
      });

      expect(result).toEqual({ success: true });
      expect(db.addToolLog).toHaveBeenCalledWith(1, "session-123", "Tool started", "status");
    });

    it("should reject if user does not have access to tool", async () => {
      vi.mocked(db.getUserTools).mockResolvedValue([]);

      const caller = toolsRouter.createCaller(mockContext);

      await expect(
        caller.addLog({
          toolId: 999,
          sessionId: "session-123",
          message: "Test",
          type: "log",
        })
      ).rejects.toThrow("You do not have access to this tool");
    });
  });

  describe("getLogs", () => {
    it("should return logs for authorized user", async () => {
      const mockTools = [
        { id: 1, userId: 1, key: "test-tool" },
      ];

      const mockLogs = [
        {
          id: 1,
          toolId: 1,
          sessionId: "session-123",
          message: "Tool started",
          type: "status",
          timestamp: new Date(),
          createdAt: new Date(),
        },
      ];

      vi.mocked(db.getUserTools).mockResolvedValue(mockTools as any);
      vi.mocked(db.getToolLogs).mockResolvedValue(mockLogs as any);

      const caller = toolsRouter.createCaller(mockContext);
      const result = await caller.getLogs({
        toolId: 1,
        sessionId: "session-123",
      });

      expect(result).toEqual(mockLogs);
      expect(db.getToolLogs).toHaveBeenCalledWith(1, "session-123");
    });

    it("should reject if user does not have access to tool", async () => {
      vi.mocked(db.getUserTools).mockResolvedValue([]);

      const caller = toolsRouter.createCaller(mockContext);

      await expect(
        caller.getLogs({
          toolId: 999,
          sessionId: "session-123",
        })
      ).rejects.toThrow("You do not have access to this tool");
    });
  });
});
