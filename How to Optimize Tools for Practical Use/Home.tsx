import { useAuth } from "@/_core/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { useLocation } from "wouter";
import { getLoginUrl } from "@/const";
import { Zap, Gauge, Stethoscope } from "lucide-react";

export default function Home() {
  const { user, isAuthenticated } = useAuth();
  const [, navigate] = useLocation();

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800">
        <div className="max-w-6xl mx-auto px-6 py-20">
          <div className="text-center mb-16">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-lg bg-blue-600 mb-6">
              <span className="text-2xl">⚙️</span>
            </div>
            <h1 className="text-5xl font-bold text-white mb-4 tracking-tight">
              SB Toolsmith
            </h1>
            <p className="text-xl text-slate-400 mb-8 max-w-2xl mx-auto">
              Elegant tool registry and management dashboard for Python developers.
              Register, install, and execute your tools with full visibility and control.
            </p>
            <a href={getLoginUrl()}>
              <Button size="lg" className="bg-blue-600 hover:bg-blue-700">
                Sign In to Get Started
              </Button>
            </a>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-20">
            <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-8">
              <Zap className="w-8 h-8 text-blue-400 mb-4" />
              <h3 className="text-lg font-semibold text-white mb-2">Quick Registration</h3>
              <p className="text-slate-400">
                Register Python tools from files, directories, or archives instantly.
              </p>
            </div>
            <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-8">
              <Gauge className="w-8 h-8 text-blue-400 mb-4" />
              <h3 className="text-lg font-semibold text-white mb-2">Full Control</h3>
              <p className="text-slate-400">
                Install with pip, poetry, or uv. Run with arguments. Monitor execution.
              </p>
            </div>
            <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-8">
              <Stethoscope className="w-8 h-8 text-blue-400 mb-4" />
              <h3 className="text-lg font-semibold text-white mb-2">Rich Diagnostics</h3>
              <p className="text-slate-400">
                Doctor/Diagnostics reveal entrypoints, dependencies, and health status.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-6xl mx-auto px-6 py-20">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-2">Welcome, {user?.name || "Developer"}</h1>
          <p className="text-muted-foreground mb-8">
            Ready to manage your Python tools?
          </p>
          <Button
            size="lg"
            onClick={() => navigate("/tools")}
            className="bg-blue-600 hover:bg-blue-700"
          >
            Open Tools Dashboard
          </Button>
        </div>
      </div>
    </div>
  );
}
