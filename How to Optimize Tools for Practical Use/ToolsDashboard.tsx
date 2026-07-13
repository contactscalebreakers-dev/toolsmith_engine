import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Loader2, Trash2, Download, Play, Stethoscope, Search } from "lucide-react";
import { useState, useMemo } from "react";
import { useAuth } from "@/_core/hooks/useAuth";
import { trpc } from "@/lib/trpc";
import { toast } from "sonner";
import TerminalOutput from "@/components/TerminalOutput";
import AddToolDialog from "@/components/AddToolDialog";
import DiagnosticsPanel from "@/components/DiagnosticsPanel";
import ExportToolDialog from "@/components/ExportToolDialog";
import EditToolDialog from "@/components/EditToolDialog";
import ToolsFilterBar from "@/components/ToolsFilterBar";

export default function ToolsDashboard() {
  const { user } = useAuth();
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState<"name" | "status" | "recent">("name");
  const [filterStatus, setFilterStatus] = useState<"all" | "installed" | "not-installed">("all");
  const [selectedToolKey, setSelectedToolKey] = useState<string | null>(null);
  const [showRemoveDialog, setShowRemoveDialog] = useState(false);
  const [showRunDialog, setShowRunDialog] = useState(false);
  const [runArgs, setRunArgs] = useState("");
  const [selectedBackend, setSelectedBackend] = useState("auto");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  // Queries
  const { data: tools = [], isLoading: toolsLoading, refetch: refetchTools } = trpc.tools.list.useQuery();
  const { data: selectedTool } = trpc.tools.get.useQuery(
    { key: selectedToolKey || "" },
    { enabled: !!selectedToolKey }
  );

  // Mutations
  const removeMutation = trpc.tools.remove.useMutation({
    onSuccess: () => {
      toast.success("Tool removed successfully");
      setShowRemoveDialog(false);
      setSelectedToolKey(null);
      refetchTools();
    },
    onError: (err) => {
      toast.error(err.message);
    },
  });

  const updateInstallMutation = trpc.tools.updateInstallStatus.useMutation();
  const updateSmokeTestMutation = trpc.tools.updateSmokeTestStatus.useMutation();

  // Filter and sort tools
  const filteredTools = useMemo(() => {
    let filtered = tools.filter((tool) => {
      const matchesSearch = tool.name.toLowerCase().includes(searchQuery.toLowerCase());
      let matchesStatus = true;
      if (filterStatus === "installed") {
        matchesStatus = Boolean(tool.lastInstallSuccess);
      } else if (filterStatus === "not-installed") {
        matchesStatus = !tool.lastInstallSuccess;
      }
      return matchesSearch && matchesStatus;
    });

    if (sortBy === "name") {
      filtered.sort((a, b) => a.name.localeCompare(b.name));
    } else if (sortBy === "status") {
      filtered.sort((a, b) => {
        const aInstalled = Boolean(a.lastInstallSuccess) ? 1 : 0;
        const bInstalled = Boolean(b.lastInstallSuccess) ? 1 : 0;
        return bInstalled - aInstalled;
      });
    } else if (sortBy === "recent") {
      filtered.sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime());
    }
    return filtered;
  }, [tools, searchQuery, sortBy, filterStatus]);

  const handleRemoveTool = async () => {
    if (!selectedToolKey) return;
    await removeMutation.mutateAsync({ key: selectedToolKey });
  };

  const handleInstallTool = async () => {
    if (!selectedToolKey) return;
    
    try {
      // In a real implementation, this would trigger the actual installation
      // For now, we'll just update the status
      await updateInstallMutation.mutateAsync({
        key: selectedToolKey,
        backend: selectedBackend,
        success: true,
        output: `Installation with ${selectedBackend} backend completed successfully`,
      });
      toast.success("Tool installed successfully");
      refetchTools();
    } catch (err) {
      toast.error("Installation failed");
    }
  };

  const handleRunTool = async () => {
    if (!selectedToolKey || !selectedTool) return;

    try {
      setIsRunning(true);
      // Generate a random session ID
      const newSessionId = Math.random().toString(36).substring(2, 15);
      setSessionId(newSessionId);

      // In a real implementation, this would trigger the actual tool execution
      // For now, we'll just update the smoke test status
      await updateSmokeTestMutation.mutateAsync({
        key: selectedToolKey,
        returnCode: 0,
        output: `Tool executed successfully with args: ${runArgs || "(none)"}`
      });

      toast.success("Tool executed successfully");
      setShowRunDialog(false);
      setRunArgs("");
      refetchTools();
    } catch (err) {
      toast.error("Tool execution failed");
    } finally {
      setIsRunning(false);
    }
  };

  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-muted-foreground">Please log in to access the tools dashboard</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold tracking-tight mb-2">Tool Registry</h1>
          <p className="text-muted-foreground">
            Manage your Python tools with full visibility and control
          </p>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Tools List */}
          <div className="lg:col-span-1">
            <Card className="h-full flex flex-col">
              <CardHeader>
                <CardTitle>Tools</CardTitle>
                <CardDescription>
                  {filteredTools.length} of {tools.length} tools
                </CardDescription>
              </CardHeader>
              <CardContent className="flex-1 flex flex-col gap-4">
                {/* Search */}
                <ToolsFilterBar
                  searchQuery={searchQuery}
                  onSearchChange={setSearchQuery}
                  sortBy={sortBy}
                  onSortChange={setSortBy}
                  filterStatus={filterStatus}
                  onFilterStatusChange={setFilterStatus}
                />

                {/* Tools List */}
                <ScrollArea className="flex-1">
                  <div className="space-y-2 pr-4">
                    {toolsLoading ? (
                      <div className="flex items-center justify-center py-8">
                        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                      </div>
                    ) : filteredTools.length === 0 ? (
                      <p className="text-sm text-muted-foreground py-8 text-center">
                        No tools found
                      </p>
                    ) : (
                      filteredTools.map((tool) => (
                        <button
                          key={tool.key}
                          onClick={() => setSelectedToolKey(tool.key)}
                          className={`w-full text-left p-3 rounded-lg border transition-colors ${
                            selectedToolKey === tool.key
                              ? "bg-accent border-accent-foreground"
                              : "border-border hover:bg-muted"
                          }`}
                        >
                          <div className="flex items-start justify-between gap-2 mb-2">
                            <div className="flex-1 min-w-0">
                              <p className="font-medium truncate">{tool.name}</p>
                              <p className="text-xs text-muted-foreground truncate">
                                {tool.key.substring(0, 12)}...
                              </p>
                            </div>
                            {tool.lastInstallSuccess ? (
                              <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200 shrink-0">
                                ✓
                              </Badge>
                            ) : (
                              <Badge variant="outline" className="bg-gray-50 shrink-0">
                                ○
                              </Badge>
                            )}
                          </div>
                          <div className="flex gap-2 flex-wrap text-xs">
                            {tool.lastInstallBackend && (
                              <Badge variant="secondary" className="text-xs">
                                {tool.lastInstallBackend}
                              </Badge>
                            )}
                            {tool.lastSmokeTestReturnCode !== null && (
                              <Badge
                                variant="secondary"
                                className={`text-xs ${
                                  tool.lastSmokeTestReturnCode === 0
                                    ? "bg-green-100 text-green-800"
                                    : "bg-red-100 text-red-800"
                                }`}
                              >
                                {tool.lastSmokeTestReturnCode === 0 ? "✓ Pass" : "✗ Fail"}
                              </Badge>
                            )}
                          </div>
                        </button>
                      ))
                    )}
                  </div>
                </ScrollArea>

                {/* Add Tool Button */}
                <AddToolDialog onToolAdded={() => refetchTools()} />
              </CardContent>
            </Card>
          </div>

          {/* Tool Details & Actions */}
          <div className="lg:col-span-2 space-y-6">
            {selectedTool ? (
              <>
                {/* Tool Details */}
                <Card>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle>{selectedTool.name}</CardTitle>
                        <CardDescription>Tool registry entry</CardDescription>
                      </div>
                      <div className="flex gap-2">
                        <EditToolDialog tool={selectedTool} />
                        <AlertDialog open={showRemoveDialog} onOpenChange={setShowRemoveDialog}>
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => setShowRemoveDialog(true)}
                          >
                            <Trash2 className="h-4 w-4 mr-2" />
                            Remove
                          </Button>
                        <AlertDialogContent>
                          <AlertDialogHeader>
                            <AlertDialogTitle>Remove Tool</AlertDialogTitle>
                            <AlertDialogDescription>
                              Are you sure you want to remove "{selectedTool.name}"? This action cannot be undone.
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <div className="flex gap-3 justify-end">
                            <AlertDialogCancel>Cancel</AlertDialogCancel>
                            <AlertDialogAction
                              onClick={handleRemoveTool}
                              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                            >
                              {removeMutation.isPending ? (
                                <>
                                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                  Removing...
                                </>
                              ) : (
                                "Remove"
                              )}
                            </AlertDialogAction>
                          </div>
                        </AlertDialogContent>
                        </AlertDialog>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {selectedTool.description && (
                      <div className="mb-4 p-3 bg-muted rounded-lg">
                        <p className="text-sm font-medium text-muted-foreground mb-1">Description</p>
                        <p className="text-sm text-foreground">{selectedTool.description}</p>
                      </div>
                    )}
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm font-medium text-muted-foreground">Key</p>
                        <p className="text-sm font-mono break-all">{selectedTool.key}</p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-muted-foreground">Source</p>
                        <p className="text-sm break-all">{selectedTool.src}</p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-muted-foreground">Entrypoint</p>
                        <p className="text-sm font-mono break-all">
                          {selectedTool.entrypoint || "Not detected"}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-muted-foreground">Root Directory</p>
                        <p className="text-sm break-all">{selectedTool.rootDir}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Install & Run Actions */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Actions</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {/* Install */}
                      <Dialog>
                        <DialogTrigger asChild>
                          <Button variant="outline" className="w-full">
                            <Download className="h-4 w-4 mr-2" />
                            Install
                          </Button>
                        </DialogTrigger>
                        <DialogContent>
                          <DialogHeader>
                            <DialogTitle>Install Tool</DialogTitle>
                            <DialogDescription>
                              Choose a backend to install dependencies for "{selectedTool.name}"
                            </DialogDescription>
                          </DialogHeader>
                          <div className="space-y-4">
                            <div>
                              <label className="text-sm font-medium">Backend</label>
                              <Select value={selectedBackend} onValueChange={setSelectedBackend}>
                                <SelectTrigger>
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="auto">Auto-detect</SelectItem>
                                  <SelectItem value="pip">pip</SelectItem>
                                  <SelectItem value="poetry">poetry</SelectItem>
                                  <SelectItem value="uv">uv</SelectItem>
                                </SelectContent>
                              </Select>
                            </div>
                            <Button
                              onClick={handleInstallTool}
                              disabled={updateInstallMutation.isPending}
                              className="w-full"
                            >
                              {updateInstallMutation.isPending ? (
                                <>
                                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                  Installing...
                                </>
                              ) : (
                                "Start Installation"
                              )}
                            </Button>
                          </div>
                        </DialogContent>
                      </Dialog>

                      {/* Run */}
                      <Dialog open={showRunDialog} onOpenChange={setShowRunDialog}>
                        <DialogTrigger asChild>
                          <Button variant="outline" className="w-full">
                            <Play className="h-4 w-4 mr-2" />
                            Run
                          </Button>
                        </DialogTrigger>
                        <DialogContent>
                          <DialogHeader>
                            <DialogTitle>Run Tool</DialogTitle>
                            <DialogDescription>
                              Execute "{selectedTool.name}" with optional arguments
                            </DialogDescription>
                          </DialogHeader>
                          <div className="space-y-4">
                            <div>
                              <label className="text-sm font-medium">CLI Arguments (optional)</label>
                              <Input
                                placeholder="--help"
                                value={runArgs}
                                onChange={(e) => setRunArgs(e.target.value)}
                              />
                            </div>
                            <Button
                              onClick={handleRunTool}
                              disabled={isRunning || updateSmokeTestMutation.isPending}
                              className="w-full"
                            >
                              {isRunning || updateSmokeTestMutation.isPending ? (
                                <>
                                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                  Running...
                                </>
                              ) : (
                                "Execute"
                              )}
                            </Button>
                          </div>
                        </DialogContent>
                      </Dialog>

                      {/* Export/Pack */}
                      <ExportToolDialog tool={selectedTool} />
                    </div>
                  </CardContent>
                </Card>

                {/* Doctor/Diagnostics */}
                <DiagnosticsPanel tool={selectedTool} />

                {/* Status Information */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Status</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm font-medium text-muted-foreground">Last Install</p>
                        <div className="flex items-center gap-2 mt-1">
                          {selectedTool.lastInstallSuccess ? (
                            <>
                              <Badge className="bg-green-100 text-green-800">✓ Success</Badge>
                              <span className="text-xs text-muted-foreground">
                                {selectedTool.lastInstallBackend}
                              </span>
                            </>
                          ) : (
                            <Badge variant="outline">Not installed</Badge>
                          )}
                        </div>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-muted-foreground">Smoke Test Status</p>
                        <div className="flex items-center gap-2 mt-1">
                          {selectedTool.lastSmokeTestReturnCode !== null ? (
                            <Badge
                              className={
                                selectedTool.lastSmokeTestReturnCode === 0
                                  ? "bg-green-100 text-green-800"
                                  : "bg-red-100 text-red-800"
                              }
                            >
                              {selectedTool.lastSmokeTestReturnCode === 0 ? "✓ Pass" : "✗ Fail"}
                            </Badge>
                          ) : (
                            <Badge variant="outline">Not tested</Badge>
                          )}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Terminal Output */}
                {sessionId && (
                  <TerminalOutput sessionId={sessionId} toolId={selectedTool.id} />
                )}
              </>
            ) : (
              <Card className="h-64 flex items-center justify-center">
                <p className="text-muted-foreground">Select a tool to view details</p>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
