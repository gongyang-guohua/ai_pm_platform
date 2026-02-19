"use client";

import { useEffect, useState } from "react";
import { LayoutDashboard, PlusCircle, Settings, LogOut, Bell, Search, Menu, Moon, Sun, Monitor, Upload } from "lucide-react";
import { cn } from "@/lib/utils";
import axios from "axios";
import ProjectCreationWizard from "@/components/ProjectCreationWizard";
import ProjectDashboard from "@/components/ProjectDashboard";
import ProjectDetailView from "@/components/ProjectDetailView";
import ManagementDashboard from "@/components/ManagementDashboard";
import ProjectListView from "@/components/ProjectListView";
import TaskListView from "@/components/TaskListView";
import ProjectImportWizard from "@/components/ProjectImportWizard";

export default function Home() {
  const [health, setHealth] = useState<string>("Loading...");
  const [view, setView] = useState<"big-screen" | "projects" | "tasks" | "create" | "detail" | "import">("big-screen");
  const [projects, setProjects] = useState<any[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  useEffect(() => {
    let apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';

    // Auto-adjust if the user is on localhost but the API is on 127.0.0.1 or vice-versa
    if (typeof window !== "undefined") {
      const currentHost = window.location.hostname;
      if (currentHost === "localhost" && apiUrl.includes("127.0.0.1")) {
        apiUrl = apiUrl.replace("127.0.0.1", "localhost");
      } else if (currentHost === "127.0.0.1" && apiUrl.includes("localhost")) {
        apiUrl = apiUrl.replace("localhost", "127.0.0.1");
      }
    }

    const fetchData = async () => {
      try {
        const res = await axios.get(`${apiUrl}/projects/`);
        setProjects(res.data);
      } catch (err: any) {
        console.error("Global project fetch failed:", err);
        setHealth(`Error: ${err.message}`);
      }
    };

    fetchData();

    axios.get(apiUrl.replace('/api/v1', '/health'))
      .then((res) => setHealth(res.data.status))
      .catch(() => setHealth("Backend unreachable"));

    // Set initial theme
    document.documentElement.classList.toggle('dark', isDarkMode);
  }, [isDarkMode]);

  const toggleTheme = () => {
    setIsDarkMode(!isDarkMode);
    document.documentElement.classList.toggle('dark', !isDarkMode);
  };

  const handleSelectProject = (id: number) => {
    setSelectedProjectId(id);
    setView("detail");
  };

  const handleDeleteProject = async (id: number) => {
    if (!confirm("Permanently delete this project?")) return;
    try {
      let apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';
      await axios.delete(`${apiUrl}/projects/${id}`);
      setProjects(projects.filter(p => p.id !== id));
      if (selectedProjectId === id) {
        setSelectedProjectId(null);
        setView("projects");
      }
    } catch (err: any) {
      if (err.response && err.response.status === 404) {
        // Already deleted or not found, just remove from list
        setProjects(projects.filter(p => p.id !== id));
        if (selectedProjectId === id) {
          setSelectedProjectId(null);
          setView("projects");
        }
      } else {
        console.error("Delete project failed:", err);
      }
    }
  };

  const handleDeleteTask = async (taskId: number) => {
    if (!confirm("Permanently delete this task?")) return;
    try {
      let apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';
      await axios.delete(`${apiUrl}/tasks/${taskId}`);
      // Refresh projects to get updated task lists
      const res = await axios.get(`${apiUrl}/projects/`);
      setProjects(res.data);
    } catch (err) {
      console.error("Delete task failed:", err);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex font-sans selection:bg-primary selection:text-primary-foreground">
      {/* Sidebar - Bloomberg Terminal Style */}
      <aside className={cn("bg-card border-r border-border flex flex-col hidden md:flex transition-all duration-300", isSidebarCollapsed ? "w-16" : "w-56")}>
        <div className="h-16 flex items-center px-4 border-b border-border justify-between">
          {!isSidebarCollapsed && (
            <h1 className="text-xl font-black italic tracking-tighter flex items-center gap-2">
              <Monitor className="w-5 h-5 text-primary" />
              V-PM PRO
            </h1>
          )}
          <button
            onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
            className="p-1 hover:bg-muted rounded text-muted-foreground"
            title={isSidebarCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
          >
            <Menu className="w-5 h-5" />
          </button>
        </div>

        <nav className="flex-1 p-2 space-y-1 mt-4">
          {!isSidebarCollapsed && <div className="px-4 mb-2 text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/50">Intelligence Center</div>}
          <SidebarButton
            active={view === "big-screen"}
            onClick={() => setView("big-screen")}
            label="Control Center"
            icon={Monitor}
            collapsed={isSidebarCollapsed}
          />
          {!isSidebarCollapsed && <div className="px-4 mt-6 mb-2 text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/50">Engineering Log</div>}
          <SidebarButton
            active={view === "projects"}
            onClick={() => setView("projects")}
            label="Project Inventory"
            icon={LayoutDashboard}
            collapsed={isSidebarCollapsed}
          />
          <SidebarButton
            active={view === "tasks"}
            onClick={() => setView("tasks")}
            label="Tasks"
            icon={Search}
            collapsed={isSidebarCollapsed}
          />
          {!isSidebarCollapsed && <div className="px-4 mt-6 mb-2 text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/50">Operations</div>}
          <SidebarButton
            active={view === "create"}
            onClick={() => setView("create")}
            label="Deployment Init"
            icon={PlusCircle}
            collapsed={isSidebarCollapsed}
          />
          <SidebarButton
            active={view === "import"}
            onClick={() => setView("import")}
            label="Import Plan"
            icon={Upload}
            collapsed={isSidebarCollapsed}
          />
          <SidebarButton
            active={false}
            onClick={() => alert("Node Configuration: Cluster Health [OK] - Node Management feature coming in v2.0")}
            label="Node Config"
            icon={Settings}
            collapsed={isSidebarCollapsed}
          />
        </nav>

        <div className="p-4 border-t border-border">
          <div
            onClick={() => alert("User: Admin_01\nRole: Project Director\nAccess: Level 4 (Full Read/Write)\n\nProfile management coming soon.")}
            className="flex items-center gap-3 p-2 border border-border bg-muted/20 hover:bg-muted transition-colors cursor-pointer overflow-hidden"
          >
            <div className="w-6 h-6 bg-primary flex items-center justify-center text-primary-foreground text-[10px] font-black">
              JD
            </div>
            <div className={cn("flex-1 min-w-0 transition-opacity duration-300", isSidebarCollapsed ? "opacity-0 w-0 hidden" : "opacity-100")}>
              <p className="text-[10px] font-bold uppercase tracking-tighter truncate">User: Admin_01</p>
              <p className="text-[9px] text-muted-foreground uppercase opacity-50 truncate">Level_4_Access</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Container */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden bg-background">
        {/* Header - Data Rich */}
        <header className="h-16 bg-card border-b border-border px-6 flex items-center justify-between sticky top-0 z-20">
          <div className="flex items-center gap-6 flex-1">
            <button className="md:hidden p-2 text-muted-foreground hover:bg-muted border border-border">
              <Menu className="w-5 h-5" />
            </button>
            <div className="relative max-w-sm w-full hidden sm:block">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
              <input
                type="text"
                placeholder="EXECUTE SEARCH: [Project | Task | Asset]..."
                className="w-full pl-9 pr-4 py-1.5 bg-muted/30 border border-border text-[10px] font-mono tracking-tight focus:outline-none focus:border-primary transition-all placeholder:opacity-50"
              />
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 px-3 py-1 bg-muted/50 border border-border h-8">
              <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest hidden lg:inline">Heartbeat:</span>
              <div className={cn("w-1.5 h-1.5 rounded-full animate-pulse", health === "healthy" ? "bg-emerald-500" : "bg-red-500")} />
              <span className={cn("text-[9px] font-black uppercase tracking-widest", health === "healthy" ? "text-emerald-500" : "text-red-500")}>
                {health}
              </span>
            </div>

            <button
              onClick={toggleTheme}
              className="p-2 border border-border text-muted-foreground hover:bg-muted transition-colors"
              title="Toggle Optical Mode"
            >
              {isDarkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>

            <button className="p-2 border border-border text-muted-foreground hover:text-primary transition-colors relative">
              <Bell className="w-4 h-4" />
              <div className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-red-500 text-[8px] font-bold text-white flex items-center justify-center border border-background">
                4
              </div>
            </button>
          </div>
        </header>

        {/* Global Market Ticker (Engineering Metrics) */}
        <div className="h-6 bg-muted/50 border-b border-border flex items-center px-4 gap-6 overflow-hidden whitespace-nowrap whitespace-pre font-mono text-[9px] uppercase tracking-tighter">
          <span className="text-primary font-bold">Project_Progress:</span> <span className="text-emerald-500">24.5%</span>
          <span className="text-muted-foreground opacity-30">|</span>
          <span className="text-primary font-bold">SPI (Schedule):</span> <span className="text-emerald-500">1.02</span>
          <span className="text-muted-foreground opacity-30">|</span>
          <span className="text-primary font-bold">CPI (Cost):</span> <span className="text-blue-500">0.98</span>
          <span className="text-muted-foreground opacity-30">|</span>
          <span className="text-primary font-bold">Safety_Index:</span> <span className="text-emerald-500">EXCELLENT</span>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto bg-background">
          <div className="p-6 md:p-8 h-full">
            {view === "big-screen" && (
              <ManagementDashboard
                projects={projects}
                onUpdateView={(v) => setView(v)}
                onSelectProject={handleSelectProject}
              />
            )}
            {view === "projects" && (
              <ProjectListView
                projects={projects}
                onSelectProject={handleSelectProject}
                onDeleteProject={handleDeleteProject}
              />
            )}
            {view === "tasks" && (
              <TaskListView
                projects={projects}
                onDeleteTask={handleDeleteTask}
              />
            )}
            {view === "create" && (
              <div className="max-w-4xl mx-auto py-8">
                <ProjectCreationWizard />
              </div>
            )}
            {view === "detail" && selectedProjectId && (
              <ProjectDetailView
                projectId={selectedProjectId}
                onBack={() => setView("projects")}
              />
            )}
            {view === "import" && (
              <div className="max-w-4xl mx-auto py-8">
                <ProjectImportWizard
                  onImportComplete={(project) => {
                    setProjects([...projects, project]);
                    setSelectedProjectId(project.id);
                    setView("detail");
                  }}
                />
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

function SidebarButton({ active, onClick, label, icon: Icon, collapsed }: any) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full flex items-center gap-3 px-4 py-2 text-[11px] font-bold uppercase tracking-tight transition-all",
        active ? "bg-primary text-primary-foreground shadow-lg" : "text-muted-foreground hover:bg-muted",
        collapsed ? "justify-center px-2" : ""
      )}
      title={label}
    >
      <Icon className="w-4 h-4" />
      {!collapsed && label}
    </button>
  );
}
