import { nanoid } from "nanoid";
import { TRPCError } from "@trpc/server";
import { z } from "zod";
import { protectedProcedure, publicProcedure, router } from "../_core/trpc";
import {
  createTool,
  getUserTools,
  getToolByKey,
  updateTool,
  updateToolMetadata,
  deleteTool,
  addToolLog,
  getToolLogs,
} from "../db";

/**
 * Tools registry router - manages tool registration, installation, execution, and diagnostics
 */
export const toolsRouter = router({
  /**
   * List all tools for the current user
   */
  list: protectedProcedure.query(async ({ ctx }) => {
    const tools = await getUserTools(ctx.user.id);
    return tools;
  }),

  /**
   * Register a new tool with metadata
   */
  register: protectedProcedure
    .input(
      z.object({
        name: z.string().min(1),
        src: z.string(),
        toolDir: z.string(),
        rootDir: z.string(),
        entrypoint: z.string().optional(),
        key: z.string(),
      })
    )
    .mutation(async ({ ctx, input }) => {
      const existingTool = await getToolByKey(input.key);
      if (existingTool) {
        throw new TRPCError({
          code: "CONFLICT",
          message: "Tool with this key already exists",
        });
      }

      const tool = await createTool(ctx.user.id, {
        key: input.key,
        name: input.name,
        src: input.src,
        toolDir: input.toolDir,
        rootDir: input.rootDir,
        entrypoint: input.entrypoint || undefined,
      } as any);

      return tool;
    }),

  /**
   * Get details for a specific tool
   */
  get: protectedProcedure
    .input(z.object({ key: z.string() }))
    .query(async ({ ctx, input }) => {
      const tool = await getToolByKey(input.key);
      if (!tool) {
        throw new TRPCError({
          code: "NOT_FOUND",
          message: "Tool not found",
        });
      }

      if (tool.userId !== ctx.user.id) {
        throw new TRPCError({
          code: "FORBIDDEN",
          message: "You do not have access to this tool",
        });
      }

      return tool;
    }),

  /**
   * Remove a tool from the registry
   */
  remove: protectedProcedure
    .input(z.object({ key: z.string() }))
    .mutation(async ({ ctx, input }) => {
      const tool = await getToolByKey(input.key);
      if (!tool) {
        throw new TRPCError({
          code: "NOT_FOUND",
          message: "Tool not found",
        });
      }

      if (tool.userId !== ctx.user.id) {
        throw new TRPCError({
          code: "FORBIDDEN",
          message: "You do not have access to this tool",
        });
      }

      await deleteTool(input.key);
      return { success: true };
    }),

  /**
   * Update tool install status after installation
   */
  updateInstallStatus: protectedProcedure
    .input(
      z.object({
        key: z.string(),
        backend: z.string(),
        success: z.boolean(),
        output: z.string().optional(),
      })
    )
    .mutation(async ({ ctx, input }) => {
      const tool = await getToolByKey(input.key);
      if (!tool) {
        throw new TRPCError({
          code: "NOT_FOUND",
          message: "Tool not found",
        });
      }

      if (tool.userId !== ctx.user.id) {
        throw new TRPCError({
          code: "FORBIDDEN",
          message: "You do not have access to this tool",
        });
      }

      await updateTool(input.key, {
        lastInstallBackend: input.backend,
        lastInstallSuccess: input.success ? 1 : 0,
        lastInstallOutput: input.output || null,
      });

      return { success: true };
    }),

  /**
   * Update tool smoke test status after running
   */
  updateSmokeTestStatus: protectedProcedure
    .input(
      z.object({
        key: z.string(),
        returnCode: z.number(),
        output: z.string().optional(),
      })
    )
    .mutation(async ({ ctx, input }) => {
      const tool = await getToolByKey(input.key);
      if (!tool) {
        throw new TRPCError({
          code: "NOT_FOUND",
          message: "Tool not found",
        });
      }

      if (tool.userId !== ctx.user.id) {
        throw new TRPCError({
          code: "FORBIDDEN",
          message: "You do not have access to this tool",
        });
      }

      await updateTool(input.key, {
        lastSmokeTestReturnCode: input.returnCode,
        lastSmokeTestOutput: input.output || null,
      });

      return { success: true };
    }),

  /**
   * Add a log entry for tool execution
   */
  addLog: protectedProcedure
    .input(
      z.object({
        toolId: z.number(),
        sessionId: z.string(),
        message: z.string(),
        type: z.enum(["log", "success", "error", "warning", "status"]),
      })
    )
    .mutation(async ({ ctx, input }) => {
      // Verify tool ownership
      const tool = await getUserTools(ctx.user.id);
      const hasAccess = tool.some((t) => t.id === input.toolId);

      if (!hasAccess) {
        throw new TRPCError({
          code: "FORBIDDEN",
          message: "You do not have access to this tool",
        });
      }

      await addToolLog(input.toolId, input.sessionId, input.message, input.type);
      return { success: true };
    }),

  /**
   * Get logs for a tool execution session
   */
  getLogs: protectedProcedure
    .input(
      z.object({
        toolId: z.number(),
        sessionId: z.string(),
      })
    )
    .query(async ({ ctx, input }) => {
      // Verify tool ownership
      const tool = await getUserTools(ctx.user.id);
      const hasAccess = tool.some((t) => t.id === input.toolId);

      if (!hasAccess) {
        throw new TRPCError({
          code: "FORBIDDEN",
          message: "You do not have access to this tool",
        });
      }

      const logs = await getToolLogs(input.toolId, input.sessionId);
      return logs;
    }),

  /**
   * Get diagnostics for a tool
   */
  diagnostics: protectedProcedure
    .input(z.object({ key: z.string() }))
    .query(async ({ ctx, input }) => {
      const tool = await getToolByKey(input.key);
      if (!tool) {
        throw new TRPCError({
          code: "NOT_FOUND",
          message: "Tool not found",
        });
      }
      if (tool.userId !== ctx.user.id) {
        throw new TRPCError({
          code: "FORBIDDEN",
          message: "You do not have access to this tool",
        });
      }

      // In production, this would analyze the tool directory/file
      // For now, return simulated diagnostics
      return {
        key: tool.key,
        name: tool.name,
        entrypoint: tool.entrypoint || "main.py",
        availableBackends: ["pip", "poetry", "uv"],
        detectedDependencyFiles: ["requirements.txt", "pyproject.toml"],
        inferredRequirements: ["requests", "click", "pydantic"],
        pythonVersion: "3.9+",
        lastHealthCheck: new Date().toISOString(),
      };
    }),

  /**
   * Update tool metadata (name and description)
   */
  updateMetadata: protectedProcedure
    .input(
      z.object({
        key: z.string(),
        name: z.string().min(1),
        description: z.string().optional(),
      })
    )
    .mutation(async ({ ctx, input }) => {
      const tool = await getToolByKey(input.key);
      if (!tool) {
        throw new TRPCError({
          code: "NOT_FOUND",
          message: "Tool not found",
        });
      }
      if (tool.userId !== ctx.user.id) {
        throw new TRPCError({
          code: "FORBIDDEN",
          message: "You do not have access to this tool",
        });
      }
      await updateToolMetadata(input.key, input.name, input.description);
      return { success: true };
    }),
  /**
   * Generate a new session ID for tool execution
   */
  generateSessionId: protectedProcedure.query(() => {
    return { sessionId: nanoid() };
  }),
});
