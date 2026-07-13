import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Stethoscope, CheckCircle, AlertCircle, FileText, RefreshCw, Loader2 } from "lucide-react";
import { useState } from "react";
import { trpc } from "@/lib/trpc";
import { toast } from "sonner";

interface DiagnosticsPanelProps {
  tool: {
    key: string;
    name: string;
    entrypoint?: string | null;
    src?: string;
    lastInstallBackend?: string | null;
    lastInstallSuccess?: number | null | boolean;
    lastSmokeTestReturnCode?: number | null;
  };
}

export default function DiagnosticsPanel({ tool }: DiagnosticsPanelProps) {
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Fetch diagnostics from backend
  const { data: diagnostics, isLoading, refetch } = trpc.tools.diagnostics.useQuery(
    { key: tool.key },
    { enabled: !!tool.key }
  );

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await refetch();
      toast.success("Diagnostics refreshed");
    } catch (error) {
      toast.error("Failed to refresh diagnostics");
    } finally {
      setIsRefreshing(false);
    }
  };

  const isHealthy =
    (tool.lastInstallSuccess === 1 || tool.lastInstallSuccess === true) &&
    tool.lastSmokeTestReturnCode === 0;

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Stethoscope className="h-5 w-5 text-blue-600" />
            <div>
              <CardTitle>Doctor/Diagnostics</CardTitle>
              <CardDescription>Tool health and configuration analysis</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Stethoscope className="h-5 w-5 text-blue-600" />
            <div>
              <CardTitle>Doctor/Diagnostics</CardTitle>
              <CardDescription>Tool health and configuration analysis</CardDescription>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            <RefreshCw className={`h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`} />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Health Status */}
        <div>
          <div className="flex items-center gap-2 mb-2">
            {isHealthy ? (
              <CheckCircle className="h-5 w-5 text-green-600" />
            ) : (
              <AlertCircle className="h-5 w-5 text-yellow-600" />
            )}
            <h4 className="font-medium">Overall Health</h4>
          </div>
          <p className="text-sm text-muted-foreground">
            {isHealthy
              ? "Tool is in good health with successful installation and smoke tests."
              : "Tool may need attention. Check installation and smoke test results."}
          </p>
        </div>

        {/* Detected Entrypoint */}
        {diagnostics?.entrypoint && (
          <div>
            <h4 className="font-medium text-sm mb-2">Detected Entrypoint</h4>
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-muted-foreground" />
              <code className="text-sm bg-muted px-2 py-1 rounded font-mono">
                {diagnostics.entrypoint}
              </code>
            </div>
          </div>
        )}

        {/* Available Backends */}
        {diagnostics?.availableBackends && diagnostics.availableBackends.length > 0 && (
          <div>
            <h4 className="font-medium text-sm mb-2">Available Backends</h4>
            <div className="flex flex-wrap gap-2">
              {diagnostics.availableBackends.map((backend) => (
                <Badge
                  key={backend}
                  variant={tool.lastInstallBackend === backend ? "default" : "outline"}
                  className="text-xs"
                >
                  {backend}
                  {tool.lastInstallBackend === backend && " (used)"}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Dependency Files */}
        {diagnostics?.detectedDependencyFiles && diagnostics.detectedDependencyFiles.length > 0 && (
          <div>
            <h4 className="font-medium text-sm mb-2">Dependency Files Found</h4>
            <div className="space-y-1">
              {diagnostics.detectedDependencyFiles.map((file) => (
                <div key={file} className="flex items-center gap-2 text-sm">
                  <CheckCircle className="h-3 w-3 text-green-600" />
                  <code className="font-mono text-xs bg-muted px-2 py-1 rounded">
                    {file}
                  </code>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Inferred Requirements */}
        {diagnostics?.inferredRequirements && diagnostics.inferredRequirements.length > 0 && (
          <div>
            <h4 className="font-medium text-sm mb-2">Inferred Requirements</h4>
            <div className="flex flex-wrap gap-2">
              {diagnostics.inferredRequirements.map((req) => (
                <Badge key={req} variant="secondary" className="text-xs">
                  {req}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Python Version */}
        {diagnostics?.pythonVersion && (
          <div>
            <h4 className="font-medium text-sm mb-2">Python Version</h4>
            <p className="text-sm text-muted-foreground">{diagnostics.pythonVersion}</p>
          </div>
        )}

        {/* Last Health Check */}
        {diagnostics?.lastHealthCheck && (
          <div className="pt-2 border-t">
            <p className="text-xs text-muted-foreground">
              Last health check:{" "}
              {new Date(diagnostics.lastHealthCheck).toLocaleString()}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
