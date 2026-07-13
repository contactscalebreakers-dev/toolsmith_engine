import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Plus, Loader2, AlertCircle } from "lucide-react";
import { trpc } from "@/lib/trpc";
import { toast } from "sonner";

interface AddToolDialogProps {
  onToolAdded?: () => void;
}

export default function AddToolDialog({ onToolAdded }: AddToolDialogProps) {
  const [open, setOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<"path" | "directory">("path");
  const [toolKey, setToolKey] = useState("");
  const [toolName, setToolName] = useState("");
  const [toolPath, setToolPath] = useState("");
  const [entrypoint, setEntrypoint] = useState("main.py");
  const [isLoading, setIsLoading] = useState(false);

  const registerMutation = trpc.tools.register.useMutation();

  const handleRegister = async () => {
    if (!toolKey.trim()) {
      toast.error("Tool key is required");
      return;
    }
    if (!toolName.trim()) {
      toast.error("Tool name is required");
      return;
    }
    if (!toolPath.trim()) {
      toast.error("Tool path is required");
      return;
    }

    setIsLoading(true);
    try {
      await registerMutation.mutateAsync({
        key: toolKey.trim(),
        name: toolName.trim(),
        src: toolPath.trim(),
        toolDir: toolPath.trim(),
        rootDir: toolPath.trim(),
        entrypoint: entrypoint.trim() || "main.py",
      });

      toast.success(`Tool "${toolName}" registered successfully`);
      setToolKey("");
      setToolName("");
      setToolPath("");
      setEntrypoint("main.py");
      setOpen(false);
      onToolAdded?.();
    } catch (error: any) {
      toast.error(error.message || "Failed to register tool");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="w-full" size="sm">
          <Plus className="h-4 w-4 mr-2" />
          Add Tool
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Add New Tool</DialogTitle>
          <DialogDescription>
            Register a Python tool by providing its path and metadata
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as "path" | "directory")}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="path">File Path</TabsTrigger>
            <TabsTrigger value="directory">Directory</TabsTrigger>
          </TabsList>

          <TabsContent value="path" className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="tool-key">Tool Key</Label>
              <Input
                id="tool-key"
                placeholder="e.g., my-awesome-tool"
                value={toolKey}
                onChange={(e) => setToolKey(e.target.value)}
                disabled={isLoading}
              />
              <p className="text-xs text-muted-foreground">
                Unique identifier for this tool (lowercase, hyphens allowed)
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="tool-name">Tool Name</Label>
              <Input
                id="tool-name"
                placeholder="e.g., My Awesome Tool"
                value={toolName}
                onChange={(e) => setToolName(e.target.value)}
                disabled={isLoading}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="tool-path">File Path</Label>
              <Input
                id="tool-path"
                placeholder="/path/to/tool.py"
                value={toolPath}
                onChange={(e) => setToolPath(e.target.value)}
                disabled={isLoading}
              />
              <p className="text-xs text-muted-foreground">
                Absolute path to the Python file
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="entrypoint">Entrypoint</Label>
              <Input
                id="entrypoint"
                placeholder="main.py"
                value={entrypoint}
                onChange={(e) => setEntrypoint(e.target.value)}
                disabled={isLoading}
              />
              <p className="text-xs text-muted-foreground">
                Main entry point file (default: main.py)
              </p>
            </div>
          </TabsContent>

          <TabsContent value="directory" className="space-y-4">
            <div className="flex items-start gap-3 p-3 bg-blue-50 dark:bg-blue-950 rounded-lg border border-blue-200 dark:border-blue-800">
              <AlertCircle className="h-5 w-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-blue-800 dark:text-blue-200">
                <p className="font-medium mb-1">Directory Registration</p>
                <p>
                  Point to a directory containing your Python project. The system will auto-detect
                  the entrypoint and dependencies.
                </p>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="tool-key-dir">Tool Key</Label>
              <Input
                id="tool-key-dir"
                placeholder="e.g., my-awesome-tool"
                value={toolKey}
                onChange={(e) => setToolKey(e.target.value)}
                disabled={isLoading}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="tool-name-dir">Tool Name</Label>
              <Input
                id="tool-name-dir"
                placeholder="e.g., My Awesome Tool"
                value={toolName}
                onChange={(e) => setToolName(e.target.value)}
                disabled={isLoading}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="dir-path">Directory Path</Label>
              <Input
                id="dir-path"
                placeholder="/path/to/project"
                value={toolPath}
                onChange={(e) => setToolPath(e.target.value)}
                disabled={isLoading}
              />
              <p className="text-xs text-muted-foreground">
                Absolute path to the project directory
              </p>
            </div>
          </TabsContent>
        </Tabs>

        <div className="flex gap-3 pt-4">
          <Button
            variant="outline"
            onClick={() => setOpen(false)}
            disabled={isLoading}
          >
            Cancel
          </Button>
          <Button
            onClick={handleRegister}
            disabled={isLoading}
            className="flex-1"
          >
            {isLoading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
            {isLoading ? "Registering..." : "Register Tool"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
