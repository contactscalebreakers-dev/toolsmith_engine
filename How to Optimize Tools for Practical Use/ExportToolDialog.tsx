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
import { Download, Loader2, CheckCircle, AlertCircle } from "lucide-react";
import { toast } from "sonner";

interface ExportToolDialogProps {
  tool: {
    key: string;
    name: string;
    src?: string;
  };
}

export default function ExportToolDialog({ tool }: ExportToolDialogProps) {
  const [open, setOpen] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [exportStatus, setExportStatus] = useState<"idle" | "exporting" | "success" | "error">(
    "idle"
  );

  const handleExport = async () => {
    setIsExporting(true);
    setExportStatus("exporting");

    try {
      // Simulate export process
      await new Promise((resolve) => setTimeout(resolve, 1500));

      // In production, this would call a backend endpoint that:
      // 1. Bundles the tool source into a .zip
      // 2. Creates a manifest.json with tool metadata
      // 3. Returns a download URL

      setExportStatus("success");
      toast.success(`Tool "${tool.name}" exported successfully`);

      // Simulate download
      setTimeout(() => {
        setOpen(false);
        setExportStatus("idle");
      }, 1000);
    } catch (error) {
      setExportStatus("error");
      toast.error("Failed to export tool");
      setTimeout(() => {
        setExportStatus("idle");
      }, 2000);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm" className="gap-2">
          <Download className="h-4 w-4" />
          Export/Pack
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[400px]">
        <DialogHeader>
          <DialogTitle>Export Tool</DialogTitle>
          <DialogDescription>
            Package "{tool.name}" as a downloadable archive
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Export Info */}
          <div className="bg-muted p-4 rounded-lg space-y-2">
            <p className="text-sm font-medium">What will be included:</p>
            <ul className="text-sm text-muted-foreground space-y-1 ml-4">
              <li>• Tool source code</li>
              <li>• Dependency files (requirements.txt, pyproject.toml, etc.)</li>
              <li>• manifest.json with tool metadata</li>
              <li>• README with setup instructions</li>
            </ul>
          </div>

          {/* Status Display */}
          {exportStatus === "exporting" && (
            <div className="flex items-center gap-2 text-sm">
              <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
              <span>Packaging tool...</span>
            </div>
          )}

          {exportStatus === "success" && (
            <div className="flex items-center gap-2 text-sm text-green-600">
              <CheckCircle className="h-4 w-4" />
              <span>Export successful! Download starting...</span>
            </div>
          )}

          {exportStatus === "error" && (
            <div className="flex items-center gap-2 text-sm text-red-600">
              <AlertCircle className="h-4 w-4" />
              <span>Export failed. Please try again.</span>
            </div>
          )}

          {/* Manifest Preview */}
          {exportStatus === "idle" && (
            <div className="bg-muted p-3 rounded text-xs font-mono space-y-1 max-h-48 overflow-y-auto">
              <div className="text-muted-foreground">
                <div>{"{"}</div>
                <div className="ml-2">
                  "name": "{tool.name}",
                </div>
                <div className="ml-2">
                  "key": "{tool.key}",
                </div>
                <div className="ml-2">
                  "version": "1.0.0",
                </div>
                <div className="ml-2">
                  "description": "Exported tool package",
                </div>
                <div className="ml-2">
                  "entrypoint": "main.py",
                </div>
                <div className="ml-2">
                  "backends": ["pip", "poetry", "uv"],
                </div>
                <div className="ml-2">
                  "created": "{new Date().toISOString()}",
                </div>
                <div>{"}"}</div>
              </div>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-3 pt-4">
          <Button
            variant="outline"
            onClick={() => setOpen(false)}
            disabled={isExporting}
          >
            Cancel
          </Button>
          <Button
            onClick={handleExport}
            disabled={isExporting || exportStatus !== "idle"}
            className="flex-1"
          >
            {isExporting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
            {exportStatus === "success" ? "Exported!" : "Export & Download"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
