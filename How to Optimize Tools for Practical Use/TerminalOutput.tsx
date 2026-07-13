import { useEffect, useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Copy, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { trpc } from "@/lib/trpc";

interface TerminalOutputProps {
  sessionId: string;
  toolId: number;
}

export default function TerminalOutput({ sessionId, toolId }: TerminalOutputProps) {
  const [logs, setLogs] = useState<string[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Fetch logs periodically
  const { data: toolLogs } = trpc.tools.getLogs.useQuery(
    { toolId, sessionId },
    { refetchInterval: 1000 }
  );

  useEffect(() => {
    if (toolLogs) {
      const formattedLogs = toolLogs.map((log) => {
        const timestamp = new Date(log.timestamp).toLocaleTimeString();
        return `[${timestamp}] ${log.message}`;
      });
      setLogs(formattedLogs);

      // Auto-scroll to bottom
      setTimeout(() => {
        if (scrollRef.current) {
          scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
      }, 0);
    }
  }, [toolLogs]);

  const handleCopy = () => {
    const text = logs.join("\n");
    navigator.clipboard.writeText(text);
    toast.success("Output copied to clipboard");
  };

  const handleClear = () => {
    setLogs([]);
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-lg">Terminal Output</CardTitle>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleCopy}
            title="Copy output"
          >
            <Copy className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClear}
            title="Clear output"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div
          ref={scrollRef}
          className="bg-slate-950 text-slate-50 rounded-lg p-4 font-mono text-sm h-64 overflow-y-auto border border-slate-800"
        >
          {logs.length === 0 ? (
            <div className="text-slate-500">Ready for output...</div>
          ) : (
            logs.map((log, idx) => (
              <div key={idx} className="whitespace-pre-wrap break-words">
                {log.includes("error") || log.includes("Error") ? (
                  <span className="text-red-400">{log}</span>
                ) : log.includes("success") || log.includes("Success") ? (
                  <span className="text-green-400">{log}</span>
                ) : log.includes("warning") || log.includes("Warning") ? (
                  <span className="text-yellow-400">{log}</span>
                ) : (
                  <span>{log}</span>
                )}
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}
