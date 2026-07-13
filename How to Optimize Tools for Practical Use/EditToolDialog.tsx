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
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Edit2, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { trpc } from "@/lib/trpc";

interface EditToolDialogProps {
  tool: {
    key: string;
    name: string;
    src?: string;
  };
  onToolUpdated?: () => void;
}

export default function EditToolDialog({ tool, onToolUpdated }: EditToolDialogProps) {
  const [open, setOpen] = useState(false);
  const [formData, setFormData] = useState({
    name: tool.name,
    description: "",
  });

  const updateMetadataMutation = trpc.tools.updateMetadata.useMutation();

  const handleSave = async () => {
    if (!formData.name.trim()) {
      toast.error("Tool name is required");
      return;
    }

    try {
      await updateMetadataMutation.mutateAsync({
        key: tool.key,
        name: formData.name,
        description: formData.description,
      });
      toast.success("Tool metadata updated successfully");
      setOpen(false);
      onToolUpdated?.();
    } catch (error) {
      toast.error("Failed to update tool metadata");
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm" className="gap-2">
          <Edit2 className="h-4 w-4" />
          Edit Metadata
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[400px]">
        <DialogHeader>
          <DialogTitle>Edit Tool Metadata</DialogTitle>
          <DialogDescription>
            Update the name and description for "{tool.name}"
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Tool Name */}
          <div className="space-y-2">
            <Label htmlFor="name">Tool Name</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) =>
                setFormData({ ...formData, name: e.target.value })
              }
              placeholder="Enter tool name"
            />
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description">Description (Optional)</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) =>
                setFormData({ ...formData, description: e.target.value })
              }
              placeholder="Enter tool description"
              rows={4}
            />
          </div>

          {/* Tool Key (Read-only) */}
          <div className="space-y-2">
            <Label htmlFor="key">Tool Key (Read-only)</Label>
            <Input
              id="key"
              value={tool.key}
              disabled
              className="bg-muted"
            />
          </div>

          {/* Tool Source (Read-only) */}
          {tool.src && (
            <div className="space-y-2">
              <Label htmlFor="src">Source Path (Read-only)</Label>
              <Input
                id="src"
                value={tool.src}
                disabled
                className="bg-muted text-xs"
              />
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-3 pt-4">
          <Button
            variant="outline"
            onClick={() => setOpen(false)}
            disabled={updateMetadataMutation.isPending}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            disabled={updateMetadataMutation.isPending}
            className="flex-1"
          >
            {updateMetadataMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
            Save Changes
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
