"use client";

import React, { useState } from "react";
import { Sidebar, SidebarBody, SidebarLink } from "@/components/ui/sidebar";
import {
  LayoutDashboard,
  ShoppingCart,
  TrendingUp,
  Calendar,
  Settings,
  Wrench,
  Package,
  FileText,
  User
} from "lucide-react";
import { ExpandableTabs } from "@/components/ui/expandable-tabs";
import { buildApiUrl, buildWsUrl, config } from "@/lib/config";

interface ProductionGateProps {
  initialAnswers: Record<string, string>;
}

export function ProductionGate({ initialAnswers }: ProductionGateProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeView, setActiveView] = useState("dashboard");
  const [backendHealth, setBackendHealth] = useState<any>(null);
  const [backendHealthError, setBackendHealthError] = useState<string | null>(null);
  const [flightCheckStatus, setFlightCheckStatus] = useState<any>(null);
  const [flightCheckRunning, setFlightCheckRunning] = useState(false);
  const [flightCheckError, setFlightCheckError] = useState<string | null>(null);

  const runFlightCheck = React.useCallback(async () => {
    setFlightCheckRunning(true);
    setFlightCheckError(null);
    try {
      const response = await fetch(buildApiUrl("/health/flight-check"));
      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        const message = `HTTP ${response.status}: ${response.statusText}`;
        setFlightCheckError(message);
        setFlightCheckStatus({
          overall_status: "error",
          timestamp: new Date().toISOString(),
          checks: errorData?.checks || {},
          errors: errorData?.errors || [{
            component: "flight_check",
            status: "error",
            message
          }]
        });
        return;
      }
      const data = await response.json();
      setFlightCheckStatus(data);

      if (data.overall_status === "error" || data.overall_status === "unhealthy" || data.overall_status === "degraded") {
        console.error("Flight check failed:", data);
      }
    } catch (error: any) {
      console.error("Failed to run flight check:", error);
      const message = error?.message || "Failed to connect to backend";
      setFlightCheckError(message);
      setFlightCheckStatus({
        overall_status: "error",
        timestamp: new Date().toISOString(),
        checks: {
          llm_providers: {
            status: "unknown",
            message: "Connection failed - backend may not be running",
            details: { error: error?.message || "Network error" }
          },
          llm_generation: {
            status: "unknown",
            message: "Cannot test - backend unreachable",
            details: { error: error?.message || "Failed to fetch" }
          },
          vector_store: {
            status: "unknown",
            message: "Cannot check - backend unreachable",
            details: { error: error?.message || "Failed to fetch" }
          },
          serpapi: {
            status: "unknown",
            message: "Cannot check - backend unreachable",
            details: { error: error?.message || "Failed to fetch" }
          },
          websocket: {
            status: "unknown",
            message: "Cannot check - backend unreachable",
            details: { error: error?.message || "Failed to fetch" }
          }
        },
        errors: [{
          component: "flight_check",
          status: "error",
          message,
          details: { error: String(error) }
        }]
      });
    } finally {
      setFlightCheckRunning(false);
    }
  }, []);

  const fetchBackendHealth = React.useCallback(async () => {
    try {
      const response = await fetch(buildApiUrl("/health"));
      if (!response.ok) {
        const message = `HTTP ${response.status}: ${response.statusText}`;
        setBackendHealthError(message);
        return;
      }
      const data = await response.json();
      setBackendHealth(data);
      setBackendHealthError(null);
    } catch (error: any) {
      const message = error?.message || "Failed to fetch backend health";
      setBackendHealthError(message);
    }
  }, []);

  // Run automatic flight check + health probe on mount
  React.useEffect(() => {
    runFlightCheck();
    fetchBackendHealth();
  }, [runFlightCheck, fetchBackendHealth]);

  const wsEnabled = backendHealth ? backendHealth.mode === "full" : null;

  const sidebarLinks = [
    {
      label: "Dashboard",
      href: "#",
      icon: <LayoutDashboard className="text-neutral-700 dark:text-neutral-200 h-5 w-5 flex-shrink-0" />,
    },
    {
      label: "Suppliers",
      href: "#",
      icon: <ShoppingCart className="text-neutral-700 dark:text-neutral-200 h-5 w-5 flex-shrink-0" />,
    },
    {
      label: "Opportunities",
      href: "#",
      icon: <TrendingUp className="text-neutral-700 dark:text-neutral-200 h-5 w-5 flex-shrink-0" />,
    },
    {
      label: "Growth Marketer",
      href: "#",
      icon: <TrendingUp className="text-neutral-700 dark:text-neutral-200 h-5 w-5 flex-shrink-0" />,
    },
    {
      label: "Events",
      href: "#",
      icon: <Calendar className="text-neutral-700 dark:text-neutral-200 h-5 w-5 flex-shrink-0" />,
    },
    {
      label: "Materials",
      href: "#",
      icon: <Package className="text-neutral-700 dark:text-neutral-200 h-5 w-5 flex-shrink-0" />,
    },
    {
      label: "Context",
      href: "#",
      icon: <FileText className="text-neutral-700 dark:text-neutral-200 h-5 w-5 flex-shrink-0" />,
    },
    {
      label: "Supervisor",
      href: "#",
      icon: <LayoutDashboard className="text-neutral-700 dark:text-neutral-200 h-5 w-5 flex-shrink-0" />,
    },
    {
      label: "Tools",
      href: "#",
      icon: <Wrench className="text-neutral-700 dark:text-neutral-200 h-5 w-5 flex-shrink-0" />,
    },
    {
      label: "Settings",
      href: "#",
      icon: <Settings className="text-neutral-700 dark:text-neutral-200 h-5 w-5 flex-shrink-0" />,
    },
  ];

  // Map sidebar link clicks to views
  const getViewFromLabel = (label: string) => {
    const mapping: Record<string, string> = {
      "Dashboard": "dashboard",
      "Suppliers": "suppliers",
      "Opportunities": "opportunities",
      "Growth Marketer": "growth marketer",
      "Events": "events",
      "Materials": "materials",
      "Context": "context",
      "Supervisor": "supervisor",
      "Tools": "tools",
      "Settings": "settings"
    };
    return mapping[label] || label.toLowerCase();
  };

  const tabs = [
    { title: "Profile", icon: User },
    { title: "Suppliers", icon: ShoppingCart },
    { title: "Opportunities", icon: TrendingUp },
    { type: "separator" as const },
    { title: "Events", icon: Calendar },
    { title: "Materials", icon: Package },
  ];

  return (
    <div className="h-screen flex bg-gray-50">
      <Sidebar open={sidebarOpen} setOpen={setSidebarOpen}>
        <SidebarBody className="justify-between gap-10">
          <div className="flex flex-col flex-1 overflow-y-auto overflow-x-hidden">
            {/* Hamburger Menu Icon (3 lines) */}
            <div className="mb-6 cursor-pointer" onClick={() => setSidebarOpen(!sidebarOpen)}>
              <div className="flex flex-col gap-1.5">
                <div className="w-6 h-0.5 bg-black" />
                <div className="w-6 h-0.5 bg-black" />
                <div className="w-6 h-0.5 bg-black" />
              </div>
            </div>

            <div className="mt-4 flex flex-col gap-2">
              {sidebarLinks.map((link, idx) => (
                <SidebarLink
                  key={idx}
                  link={link}
                  onClick={() => setActiveView(getViewFromLabel(link.label))}
                />
              ))}
            </div>
          </div>
        </SidebarBody>
      </Sidebar>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-8">
          {/* Top Navigation */}
          <div className="mb-6">
            <ExpandableTabs
              tabs={tabs}
              onChange={(index) => {
                if (index !== null) {
                  const tab = tabs[index];
                  if (tab.type !== "separator") {
                    const viewMap: Record<string, string> = {
                      "Profile": "context",
                      "Suppliers": "suppliers",
                      "Opportunities": "opportunities",
                      "Events": "events",
                      "Materials": "materials"
                    };
                    setActiveView(viewMap[tab.title] || tab.title.toLowerCase());
                  }
                }
              }}
            />
          </div>

          {/* Content based on active view */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            {activeView === "dashboard" && (
              <DashboardView answers={initialAnswers} />
            )}
            {activeView === "supervisor" && (
              <SupervisorView answers={initialAnswers} wsEnabled={wsEnabled} />
            )}
            {activeView === "tools" && (
              <ToolsView />
            )}
            {activeView === "suppliers" && (
              <SuppliersView answers={initialAnswers} />
            )}
            {activeView === "opportunities" && (
              <OpportunitiesView answers={initialAnswers} />
            )}
            {activeView === "growth marketer" && (
              <GrowthMarketerView answers={initialAnswers} />
            )}
            {activeView === "events" && (
              <EventsView answers={initialAnswers} />
            )}
            {activeView === "materials" && (
              <MaterialsView answers={initialAnswers} />
            )}
            {activeView === "context" && (
              <ContextView answers={initialAnswers} />
            )}
            {activeView === "settings" && (
              <SettingsView
                backendHealth={backendHealth}
                backendHealthError={backendHealthError}
                flightCheckStatus={flightCheckStatus}
                flightCheckRunning={flightCheckRunning}
                flightCheckError={flightCheckError}
                onRunFlightCheck={runFlightCheck}
                wsEnabled={wsEnabled}
              />
            )}
            {activeView === "profile" && (
              <ContextView answers={initialAnswers} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// View Components
function DashboardView({ answers }: { answers: Record<string, string> }) {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Dashboard</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="border border-black p-4 rounded">
          <h3 className="font-semibold">Craft Type</h3>
          <p className="text-gray-600">{answers.craft_type || "pottery"}</p>
        </div>
        <div className="border border-black p-4 rounded">
          <h3 className="font-semibold">Location</h3>
          <p className="text-gray-600">{answers.location || "Jaipur"}</p>
        </div>
        <div className="border border-black p-4 rounded">
          <h3 className="font-semibold">Business Status</h3>
          <p className="text-green-600">Ready for AI Analysis</p>
        </div>
      </div>
      <div className="mt-6">
        <p className="text-gray-700">
          Welcome to Artisan Hub! Your craft type has been detected as <strong>{answers.craft_type || "pottery"}</strong>.
          Use the sidebar to access supplier discovery, growth opportunities, and more AI-powered tools.
        </p>
      </div>
    </div>
  );
}

function SupervisorView({ answers, wsEnabled }: { answers?: Record<string, string>; wsEnabled: boolean | null }) {
  const [goal, setGoal] = React.useState("Transform my artisan business for 200% revenue growth");
  const [maxSteps, setMaxSteps] = React.useState(6);
  const [capabilities, setCapabilities] = React.useState<string[]>(["profile_analyst", "supply_hunter", "growth_marketer", "event_scout"]);
  const [running, setRunning] = React.useState(false);
  const [logs, setLogs] = React.useState<any[]>([]);
  const [results, setResults] = React.useState<any>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [wsNotice, setWsNotice] = React.useState<string | null>(null);
  const wsRef = React.useRef<WebSocket | null>(null);

  React.useEffect(() => {
    let isActive = true;
    if (wsEnabled === null) {
      return () => {
        isActive = false;
      };
    }
    if (!wsEnabled) {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      if (isActive) {
        setWsNotice("Realtime updates are disabled while the backend is in minimal mode.");
      }
      return () => {
        isActive = false;
      };
    }

    const ws = new WebSocket(buildWsUrl("/ws"));
    ws.onopen = () => ws.send(JSON.stringify({ type: "subscribe" }));
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "agent_progress") {
        setLogs(prev => [...prev, { timestamp: data.timestamp, agent: data.agent, step: data.step, message: data.message, data: data.data }]);
      }
    };
    ws.onerror = () => {
      if (isActive) {
        setWsNotice("Realtime updates unavailable (WebSocket connection error).");
      }
    };
    ws.onclose = () => {
      if (isActive) {
        setWsNotice("Realtime updates disconnected.");
      }
    };
    wsRef.current = ws;
    setWsNotice(null);
    return () => {
      isActive = false;
      ws.onopen = null;
      ws.onmessage = null;
      ws.onerror = null;
      ws.onclose = null;
      ws.close();
    };
  }, [wsEnabled]);

  const runMission = async () => {
    setRunning(true);
    setResults(null);
    setError(null);
    setLogs([]);
    try {
      const ctx = answers || JSON.parse(localStorage.getItem("questionnaireAnswers") || "{}");
      const body = {
        goal,
        context: {
          craft_type: ctx.craft_type || "pottery",
          supplies_needed: (ctx.supplies || "clay,glazes,pigments").split(",").map((s: string) => s.trim()),
          location: { city: ctx.location?.split(",")[0] || "Jaipur", state: ctx.location?.split(",")[1] || "Rajasthan" },
          current_products: (ctx.products || "plates,vases,bowls").split(",").map((s: string) => s.trim()),
          input_text: Object.values(ctx).join(" ")
        },
        constraints: { max_steps: maxSteps, step_timeout_s: 90, retries: 1, region_priority: "in-first" },
        capabilities
      };
      const resp = await fetch(buildApiUrl("/agents/supervise/run"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: `HTTP ${resp.status}` }));
        throw new Error(err.detail || `Request failed: ${resp.status}`);
      }
      const data = await resp.json();
      setResults(data);
    } catch (e: any) {
      setError(e?.message || "Mission failed");
    } finally {
      setRunning(false);
    }
  };

  // Enhanced autonomous agent execution
  const runAutonomousMission = async () => {
    setRunning(true);
    setResults(null);
    setError(null);
    setLogs([]);
    try {
      const ctx = answers || JSON.parse(localStorage.getItem("questionnaireAnswers") || "{}");
      const body = {
        goal: "Execute comprehensive autonomous business intelligence analysis",
        context: {
          craft_type: ctx.craft_type || "pottery",
          supplies_needed: (ctx.supplies || "clay,glazes,pigments").split(",").map((s: string) => s.trim()),
          location: { city: ctx.location?.split(",")[0] || "Jaipur", state: ctx.location?.split(",")[1] || "Rajasthan" },
          current_products: (ctx.products || "plates,vases,bowls").split(",").map((s: string) => s.trim()),
          input_text: Object.values(ctx).join(" "),
          autonomous_mode: true,
          intelligence_level: "maximum"
        },
        constraints: { 
          max_steps: 10, 
          step_timeout_s: 120, 
          retries: 3, 
          region_priority: "in-first",
          autonomous_execution: true
        },
        capabilities: ["profile_analyst", "supply_hunter", "growth_marketer", "event_scout"]
      };
      const resp = await fetch(buildApiUrl("/agents/god-mode/intelligence"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: `HTTP ${resp.status}` }));
        throw new Error(err.detail || `Request failed: ${resp.status}`);
      }
      const data = await resp.json();
      setResults(data);
    } catch (e: any) {
      setError(e?.message || "Autonomous mission failed");
    } finally {
      setRunning(false);
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold">Supervisor - AI Agent Orchestration</h2>
        <button
          onClick={runMission}
          disabled={running}
          className="px-4 py-2 bg-black text-white rounded hover:bg-gray-800 disabled:bg-gray-400"
        >
          {running ? "Running AI Mission..." : "Run Full AI Analysis"}
        </button>
      </div>
      {wsNotice && (
        <div className="mb-4 p-3 bg-yellow-50 border-2 border-yellow-400 rounded-lg text-yellow-800 text-sm">
          {wsNotice}
        </div>
      )}

      <div className="grid md:grid-cols-2 gap-4 mb-4">
        <div>
          <label className="block text-sm font-medium mb-1">Business Goal</label>
          <input
            value={goal}
            onChange={e => setGoal(e.target.value)}
            className="w-full border-2 border-black rounded p-2"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Max Agent Steps</label>
          <input
            type="number"
            value={maxSteps}
            onChange={e => setMaxSteps(parseInt(e.target.value || '1'))}
            className="w-full border-2 border-black rounded p-2"
          />
        </div>
      </div>

      <div className="mb-4">
        <label className="block text-sm font-medium mb-1">AI Agents to Use</label>
        <div className="flex flex-wrap gap-2">
          {[
            { key: "profile_analyst", label: "Profile Analyst" },
            { key: "supply_hunter", label: "Supply Hunter" },
            { key: "growth_marketer", label: "Growth Marketer" },
            { key: "event_scout", label: "Event Scout" },
          ].map(opt => (
            <label key={opt.key} className="flex items-center gap-2 border-2 border-black rounded px-2 py-1">
              <input
                type="checkbox"
                checked={capabilities.includes(opt.key)}
                onChange={(e) => {
                  setCapabilities(prev => e.target.checked ? [...prev, opt.key] : prev.filter(x => x !== opt.key));
                }}
              />
              <span>{opt.label}</span>
            </label>
          ))}
        </div>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border-2 border-red-500 rounded-lg">
          <div className="flex items-center gap-2">
            <span className="text-red-600 font-bold">⚠️</span>
            <p className="font-semibold text-red-800">Error: {error}</p>
          </div>
        </div>
      )}

      {logs.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-2">AI Agent Activity Log</h3>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {logs.map((log, idx) => (
              <div key={idx} className="p-3 border-2 rounded-lg border-gray-200">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold">{log.agent}</span>
                      <span className="text-xs text-gray-500">{new Date(log.timestamp).toLocaleTimeString()}</span>
                    </div>
                    <p className="text-sm mt-1">{log.message}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {results && (
        <div className="space-y-6">
          <h3 className="text-xl font-bold">AI Analysis Complete</h3>
          <div className="bg-green-50 border-2 border-green-500 rounded-lg p-4">
            <p className="text-green-800 font-semibold">🎯 Mission Results</p>
            <pre className="text-xs mt-2 overflow-auto">{JSON.stringify(results, null, 2)}</pre>
          </div>
        </div>
      )}
    </div>
  );
}

function ToolsView() {
  const [tools, setTools] = React.useState<any[]>([]);
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);

  const loadTools = async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetch(buildApiUrl("/agents/tools"));
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      setTools(data.tools || []);
    } catch (e: any) {
      setError(e?.message || "Failed to load tools");
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => { loadTools(); }, []);

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold">AI Agent Tools</h2>
        <button onClick={loadTools} disabled={loading} className="px-3 py-1 text-sm bg-black text-white rounded hover:bg-gray-800 disabled:bg-gray-400">
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </div>
      {error && (
        <div className="mb-4 p-4 bg-red-50 border-2 border-red-500 rounded-lg">
          <div className="flex items-center gap-2">
            <span className="text-red-600 font-bold">⚠️</span>
            <p className="font-semibold text-red-800">Error: {error}</p>
          </div>
        </div>
      )}
      <div className="grid gap-3">
        {tools.map((t, idx) => (
          <div key={idx} className="p-3 border-2 border-black rounded">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="font-semibold">{t.name}</h3>
                <p className="text-sm text-gray-600 mt-1">{t.description}</p>
              </div>
            </div>
          </div>
        ))}
        {tools.length === 0 && !loading && !error && (
          <p className="text-gray-600">No AI tools found.</p>
        )}
      </div>
    </div>
  );
}

function SuppliersView({ answers: propAnswers }: { answers?: Record<string, string> }) {
  const [isSearching, setIsSearching] = React.useState(false);
  const [suppliers, setSuppliers] = React.useState<any[]>([]);
  const [error, setError] = React.useState<string | null>(null);

  const startSupplierSearch = async () => {
    setIsSearching(true);
    setSuppliers([]);
    setError(null);

    try {
      const answers = propAnswers || JSON.parse(localStorage.getItem("questionnaireAnswers") || "{}");

      const response = await fetch(buildApiUrl("/agents/supply/search"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          craft_type: answers.craft_type || "pottery",
          supplies_needed: (answers.supplies || "clay,glazes").split(",").map((s: string) => s.trim()),
          location: {
            city: answers.location?.split(",")[0] || "Jaipur",
            state: answers.location?.split(",")[1] || "Rajasthan"
          }
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `HTTP ${response.status}: ${response.statusText}` }));
        throw new Error(errorData.detail || `Request failed: ${response.status}`);
      }

      const result = await response.json();
      setSuppliers(result.suppliers || []);
    } catch (error: any) {
      const errorMessage = error?.message || "Failed to search for suppliers.";
      setError(errorMessage);
      console.error("Search error:", error);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold">Supplier Discovery</h2>
        <button
          onClick={startSupplierSearch}
          disabled={isSearching}
          className="px-4 py-2 bg-black text-white rounded hover:bg-gray-800 disabled:bg-gray-400"
        >
          {isSearching ? "Searching..." : "Find Suppliers"}
        </button>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border-2 border-red-500 rounded-lg">
          <div className="flex items-center gap-2">
            <span className="text-red-600 font-bold">⚠️</span>
            <p className="font-semibold text-red-800">Error: {error}</p>
          </div>
        </div>
      )}

      {!isSearching && suppliers.length === 0 && (
        <p className="text-gray-600">Click &apos;Find Suppliers&apos; to discover suppliers for your craft materials.</p>
      )}

      {suppliers.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-2">Found Suppliers ({suppliers.length})</h3>
          <div className="grid gap-4">
            {suppliers.map((supplier, idx) => (
              <div key={idx} className="border-2 border-black p-4 rounded-lg">
                <h4 className="font-bold">{supplier.name || "Unknown Supplier"}</h4>
                {supplier.location && (
                  <p className="text-sm text-gray-600">
                    📍 {supplier.location.city}, {supplier.location.state}
                  </p>
                )}
                {supplier.products && (
                  <p className="text-sm mt-1">
                    <strong>Products:</strong> {supplier.products.join(", ")}
                  </p>
                )}
                {supplier.verification && (
                  <p className="text-sm mt-1">
                    <strong>Confidence:</strong> {(supplier.verification.confidence * 100).toFixed(0)}%
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function OpportunitiesView({ answers }: { answers?: Record<string, string> }) {
  const [isAnalyzing, setIsAnalyzing] = React.useState(false);
  const [results, setResults] = React.useState<any>(null);
  const [error, setError] = React.useState<string | null>(null);

  const analyzeOpportunities = async () => {
    setIsAnalyzing(true);
    setResults(null);
    setError(null);

    try {
      const userAnswers = answers || JSON.parse(localStorage.getItem("questionnaireAnswers") || "{}");

      const response = await fetch(buildApiUrl("/agents/growth/analyze"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          craft_type: userAnswers.craft_type || "pottery",
          specialization: "traditional handmade",
          current_products: (userAnswers.products || "plates,vases,bowls").split(",").map((s: string) => s.trim()),
          location: {
            city: userAnswers.location?.split(",")[0] || "Jaipur",
            state: userAnswers.location?.split(",")[1] || "Rajasthan"
          }
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `HTTP ${response.status}: ${response.statusText}` }));
        throw new Error(errorData.detail || `Request failed: ${response.status}`);
      }

      const result = await response.json();
      setResults(result);
    } catch (error: any) {
      const errorMessage = error?.message || "Failed to analyze opportunities.";
      setError(errorMessage);
      console.error("Analysis error:", error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold">Growth Opportunities</h2>
        <button
          onClick={analyzeOpportunities}
          disabled={isAnalyzing}
          className="px-4 py-2 bg-black text-white rounded hover:bg-gray-800 disabled:bg-gray-400"
        >
          {isAnalyzing ? "Analyzing..." : "Analyze Growth"}
        </button>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border-2 border-red-500 rounded-lg">
          <div className="flex items-center gap-2">
            <span className="text-red-600 font-bold">⚠️</span>
            <p className="font-semibold text-red-800">Error: {error}</p>
          </div>
        </div>
      )}

      {!isAnalyzing && !results && (
        <p className="text-gray-600">Click &apos;Analyze Growth&apos; to discover business opportunities for your craft.</p>
      )}

      {results && (
        <div className="space-y-6">
          <h3 className="text-xl font-bold">Growth Analysis Complete</h3>
          <pre className="text-xs bg-gray-50 p-3 border rounded overflow-auto">{JSON.stringify(results, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

function GrowthMarketerView({ answers }: { answers?: Record<string, string> }) {
  const [isAnalyzing, setIsAnalyzing] = React.useState(false);
  const [results, setResults] = React.useState<any>(null);
  const [error, setError] = React.useState<string | null>(null);

  const analyzeGrowth = async () => {
    setIsAnalyzing(true);
    setResults(null);
    setError(null);

    try {
      const userAnswers = answers || JSON.parse(localStorage.getItem("questionnaireAnswers") || "{}");

      const response = await fetch(buildApiUrl("/agents/growth/analyze"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          craft_type: userAnswers.craft_type || "pottery",
          specialization: "traditional handmade",
          current_products: (userAnswers.products || "plates,vases,bowls").split(",").map((s: string) => s.trim()),
          location: {
            city: userAnswers.location?.split(",")[0] || "Jaipur",
            state: userAnswers.location?.split(",")[1] || "Rajasthan"
          }
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `HTTP ${response.status}: ${response.statusText}` }));
        throw new Error(errorData.detail || `Request failed: ${response.status}`);
      }

      const result = await response.json();
      setResults(result);
    } catch (error: any) {
      const errorMessage = error?.message || "Failed to analyze growth.";
      setError(errorMessage);
      console.error("Analysis error:", error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold">Growth Marketer</h2>
        <button
          onClick={analyzeGrowth}
          disabled={isAnalyzing}
          className="px-4 py-2 bg-black text-white rounded hover:bg-gray-800 disabled:bg-gray-400"
        >
          {isAnalyzing ? "Analyzing..." : "Market Analysis"}
        </button>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border-2 border-red-500 rounded-lg">
          <div className="flex items-center gap-2">
            <span className="text-red-600 font-bold">⚠️</span>
            <p className="font-semibold text-red-800">Error: {error}</p>
          </div>
        </div>
      )}

      {!isAnalyzing && !results && (
        <p className="text-gray-600">Click &apos;Market Analysis&apos; to get detailed marketing insights for your craft.</p>
      )}

      {results && (
        <div className="space-y-6">
          <h3 className="text-xl font-bold">Market Analysis Complete</h3>
          <pre className="text-xs bg-gray-50 p-3 border rounded overflow-auto">{JSON.stringify(results, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

function EventsView({ answers }: { answers?: Record<string, string> }) {
  const [isSearching, setIsSearching] = React.useState(false);
  const [results, setResults] = React.useState<any>(null);
  const [error, setError] = React.useState<string | null>(null);

  const searchEvents = async () => {
    setIsSearching(true);
    setResults(null);
    setError(null);

    try {
      const userAnswers = answers || JSON.parse(localStorage.getItem("questionnaireAnswers") || "{}");

      const response = await fetch(buildApiUrl("/agents/events/search"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          craft_type: userAnswers.craft_type || "pottery",
          location: {
            city: userAnswers.location?.split(",")[0] || "Jaipur",
            state: userAnswers.location?.split(",")[1] || "Rajasthan"
          },
          travel_radius_km: 100
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `HTTP ${response.status}: ${response.statusText}` }));
        throw new Error(errorData.detail || `Request failed: ${response.status}`);
      }

      const result = await response.json();
      setResults(result);
    } catch (error: any) {
      const errorMessage = error?.message || "Failed to find events.";
      setError(errorMessage);
      console.error("Search error:", error);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold">Event Discovery</h2>
        <button
          onClick={searchEvents}
          disabled={isSearching}
          className="px-4 py-2 bg-black text-white rounded hover:bg-gray-800 disabled:bg-gray-400"
        >
          {isSearching ? "Searching..." : "Find Events"}
        </button>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border-2 border-red-500 rounded-lg">
          <div className="flex items-center gap-2">
            <span className="text-red-600 font-bold">⚠️</span>
            <p className="font-semibold text-red-800">Error: {error}</p>
          </div>
        </div>
      )}

      {!isSearching && !results && (
        <p className="text-gray-600">Click &apos;Find Events&apos; to discover craft fairs, exhibitions, and opportunities for your products.</p>
      )}

      {results && (
        <div className="space-y-6">
          <h3 className="text-xl font-bold">Events Found</h3>
          <pre className="text-xs bg-gray-50 p-3 border rounded overflow-auto">{JSON.stringify(results, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

function MaterialsView({ answers }: { answers?: Record<string, string> }) {
  const [isSearching, setIsSearching] = React.useState(false);
  const [results, setResults] = React.useState<any>(null);
  const [error, setError] = React.useState<string | null>(null);

  const searchMaterials = async () => {
    setIsSearching(true);
    setResults(null);
    setError(null);

    try {
      const userAnswers = answers || JSON.parse(localStorage.getItem("questionnaireAnswers") || "{}");

      const response = await fetch(buildApiUrl("/agents/supply/search"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          craft_type: userAnswers.craft_type || "pottery",
          supplies_needed: (userAnswers.supplies || "clay,glazes").split(",").map((s: string) => s.trim()),
          location: {
            city: userAnswers.location?.split(",")[0] || "Jaipur",
            state: userAnswers.location?.split(",")[1] || "Rajasthan"
          }
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `HTTP ${response.status}: ${response.statusText}` }));
        throw new Error(errorData.detail || `Request failed: ${response.status}`);
      }

      const result = await response.json();
      setResults(result);
    } catch (error: any) {
      const errorMessage = error?.message || "Failed to find materials.";
      setError(errorMessage);
      console.error("Search error:", error);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold">Materials & Equipment</h2>
        <button
          onClick={searchMaterials}
          disabled={isSearching}
          className="px-4 py-2 bg-black text-white rounded hover:bg-gray-800 disabled:bg-gray-400"
        >
          {isSearching ? "Searching..." : "Find Materials"}
        </button>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border-2 border-red-500 rounded-lg">
          <div className="flex items-center gap-2">
            <span className="text-red-600 font-bold">⚠️</span>
            <p className="font-semibold text-red-800">Error: {error}</p>
          </div>
        </div>
      )}

      {!isSearching && !results && (
        <p className="text-gray-600">Click &apos;Find Materials&apos; to discover suppliers for craft materials and equipment.</p>
      )}

      {results && (
        <div className="space-y-6">
          <h3 className="text-xl font-bold">Materials Found</h3>
          <pre className="text-xs bg-gray-50 p-3 border rounded overflow-auto">{JSON.stringify(results, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

function ContextView({ answers }: { answers: Record<string, string> }) {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Business Profile</h2>
      <div className="grid gap-4">
        <div className="border border-black p-4 rounded">
          <h3 className="font-semibold mb-2">Questionnaire Answers</h3>
          <div className="grid md:grid-cols-2 gap-3 text-sm">
            {Object.entries(answers).map(([key, value]) => (
              <div key={key}>
                <div className="font-semibold capitalize">{key.replace("_", " ")}</div>
                <div className="text-gray-600">{value || "Not specified"}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function SettingsView({
  backendHealth,
  backendHealthError,
  flightCheckStatus,
  flightCheckRunning,
  flightCheckError,
  onRunFlightCheck,
  wsEnabled,
}: {
  backendHealth: any;
  backendHealthError: string | null;
  flightCheckStatus: any;
  flightCheckRunning: boolean;
  flightCheckError: string | null;
  onRunFlightCheck: () => void;
  wsEnabled: boolean | null;
}) {
  const overallStatus = flightCheckStatus?.overall_status || "unknown";
  const statusTone =
    overallStatus === "healthy"
      ? "text-green-600"
      : overallStatus === "warning"
        ? "text-yellow-600"
        : overallStatus === "degraded"
          ? "text-orange-600"
          : overallStatus === "error"
            ? "text-red-600"
            : "text-gray-600";
  const checks = flightCheckStatus?.checks ? Object.entries(flightCheckStatus.checks) : [];
  const actionItems = flightCheckStatus?.action_items || flightCheckStatus?.errors || [];
  const lastRun = flightCheckStatus?.timestamp
    ? new Date(flightCheckStatus.timestamp).toLocaleString()
    : "Not run yet";

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Settings</h2>
      <div className="space-y-4">
        <div className="border-2 border-black p-4 rounded">
          <h3 className="font-semibold mb-2">Application Status</h3>
          <p className="text-sm text-gray-700">
            {backendHealth?.message || "Health check pending."}
          </p>
          <p className="text-sm text-gray-600 mt-1">
            Mode: <span className="font-semibold">{backendHealth?.mode || "unknown"}</span>
          </p>
          {backendHealthError && (
            <p className="text-sm text-red-600 mt-2">Health error: {backendHealthError}</p>
          )}
        </div>
        <div className="border-2 border-black p-4 rounded">
          <h3 className="font-semibold mb-2">API Endpoints</h3>
          <p className="text-sm text-gray-600">Backend: {config.apiUrl}</p>
          <p className="text-sm text-gray-600">
            WebSocket: {config.wsUrl} {wsEnabled === false ? "(disabled in minimal mode)" : ""}
          </p>
        </div>
        <div className="border-2 border-black p-4 rounded">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold">Flight Check</h3>
            <button
              onClick={onRunFlightCheck}
              disabled={flightCheckRunning}
              className="px-3 py-1 text-sm bg-black text-white rounded hover:bg-gray-800 disabled:bg-gray-400"
            >
              {flightCheckRunning ? "Running..." : "Run Flight Check"}
            </button>
          </div>
          {flightCheckError && (
            <p className="text-sm text-red-600 mb-2">Flight check error: {flightCheckError}</p>
          )}
          <p className={`text-sm font-semibold ${statusTone}`}>Overall status: {overallStatus}</p>
          <p className="text-sm text-gray-600">Last run: {lastRun}</p>
          {checks.length > 0 && (
            <div className="mt-3">
              <h4 className="text-sm font-semibold mb-2">Checks</h4>
              <div className="grid gap-2">
                {checks.map(([name, check]) => (
                  <div key={name} className="flex items-center justify-between text-sm border rounded px-2 py-1">
                    <span className="font-medium">{name.replace(/_/g, " ")}</span>
                    <span className="text-gray-700">{check.status}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          {actionItems.length > 0 && (
            <div className="mt-3">
              <h4 className="text-sm font-semibold mb-2">Action Items</h4>
              <div className="grid gap-2 text-sm">
                {actionItems.map((item: any, idx: number) => (
                  <div key={idx} className="border rounded px-2 py-1">
                    <div className="font-semibold">{item.component || "flight_check"}</div>
                    <div className="text-gray-700">{item.message}</div>
                    {item.suggestion && (
                      <div className="text-gray-600 mt-1">Suggestion: {item.suggestion}</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
