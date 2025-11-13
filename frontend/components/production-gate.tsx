"use client";

import React, { useState } from "react";
import { Sidebar, SidebarBody, SidebarLink } from "@/components/ui/sidebar";
import {
  LayoutDashboard,
  ShoppingCart,
  TrendingUp,
  Calendar,
  Settings,
  Package,
  FileText,
  User
} from "lucide-react";
import { ExpandableTabs } from "@/components/ui/expandable-tabs";

interface ProductionGateProps {
  initialAnswers: Record<string, string>;
}

export function ProductionGate({ initialAnswers }: ProductionGateProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeView, setActiveView] = useState("dashboard");
  const [flightCheckStatus, setFlightCheckStatus] = useState<any>(null);

  // Run automatic flight check on mount
  React.useEffect(() => {
    const runFlightCheck = async () => {
      try {
        const response = await fetch("http://localhost:8000/health/flight-check");
        if (!response.ok) {
          const errorData = await response.json().catch(() => null);
          setFlightCheckStatus({
            overall_status: "error",
            timestamp: new Date().toISOString(),
            checks: errorData?.checks || {},
            errors: errorData?.errors || [{
              component: "flight_check",
              status: "error",
              message: `HTTP ${response.status}: ${response.statusText}`
            }]
          });
          return;
        }
        const data = await response.json();
        setFlightCheckStatus(data);
        
        if (data.overall_status === "error" || data.overall_status === "unhealthy") {
          console.error("Flight check failed:", data);
        }
      } catch (error: any) {
        console.error("Failed to run flight check:", error);
        setFlightCheckStatus({
          overall_status: "error",
          timestamp: new Date().toISOString(),
          checks: {
            ollama: {
              status: "unknown",
              message: "Connection failed - backend may not be running",
              details: { error: error?.message || "Network error" }
            },
            ollama_generation: {
              status: "unknown",
              message: "Cannot test - backend unreachable",
              details: { error: error?.message || "Failed to fetch" }
            },
            chromadb: {
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
            message: error?.message || "Failed to connect to backend",
            details: { error: String(error) }
          }]
        });
      }
    };
    
    runFlightCheck();
  }, []);

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
      label: "Materials & Equipment",
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
      icon: <Settings className="text-neutral-700 dark:text-neutral-200 h-5 w-5 flex-shrink-0" />,
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
      "Materials & Equipment": "materials & equipment",
      "Supervisor": "supervisor",
      "Tools": "tools",
      "Context": "context",
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
              <SupervisorView answers={initialAnswers} />
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
            {activeView === "materials & equipment" && (
              <MaterialsView answers={initialAnswers} />
            )}
            {activeView === "materials" && (
              <MaterialsView answers={initialAnswers} />
            )}
            {activeView === "context" && (
              <ContextView answers={initialAnswers} />
            )}
            {activeView === "settings" && (
              <SettingsView />
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
          <p className="text-gray-600">{answers.craft_type || "N/A"}</p>
        </div>
        <div className="border border-black p-4 rounded">
          <h3 className="font-semibold">Location</h3>
          <p className="text-gray-600">{answers.location || "N/A"}</p>
        </div>
        <div className="border border-black p-4 rounded">
          <h3 className="font-semibold">Experience</h3>
          <p className="text-gray-600">{answers.experience || "N/A"}</p>
        </div>
      </div>
    </div>
  );
}

function SupervisorView({ answers }: { answers?: Record<string, string> }) {
  const [goal, setGoal] = React.useState("Find verified suppliers and propose next actions");
  const [maxSteps, setMaxSteps] = React.useState(5);
  const [capabilities, setCapabilities] = React.useState<string[]>(["profile_analyst", "supply_hunter", "growth_marketer", "event_scout"]);
  const [running, setRunning] = React.useState(false);
  const [plan, setPlan] = React.useState<any[]>([]);
  const [artifacts, setArtifacts] = React.useState<any[]>([]);
  const [summary, setSummary] = React.useState<string>("");
  const [error, setError] = React.useState<string | null>(null);
  const [logs, setLogs] = React.useState<any[]>([]);
  const wsRef = React.useRef<WebSocket | null>(null);

  React.useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws");
    ws.onopen = () => ws.send(JSON.stringify({ type: "subscribe" }));
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "agent_progress") {
        setLogs(prev => [...prev, { timestamp: data.timestamp, agent: data.agent, step: data.step, message: data.message, data: data.data }]);
      }
    };
    ws.onerror = () => setError("WebSocket connection error");
    wsRef.current = ws;
    return () => ws.close();
  }, []);

  const runMission = async () => {
    setRunning(true);
    setPlan([]);
    setArtifacts([]);
    setSummary("");
    setError(null);
    setLogs([]);
    try {
      const ctx = answers || JSON.parse(localStorage.getItem("questionnaireAnswers") || "{}");
      const body = {
        goal,
        context: {
          craft_type: ctx.craft_type || "pottery",
          supplies_needed: (ctx.supplies || "").split(",").map((s: string) => s.trim()).filter(Boolean),
          location: { city: ctx.location?.split(",")[0] || "Jaipur", state: ctx.location?.split(",")[1] || "Rajasthan" },
          current_products: (ctx.products || "").split(",").map((s: string) => s.trim()).filter(Boolean),
          input_text: Object.values(ctx).join(" ")
        },
        constraints: { max_steps: maxSteps, step_timeout_s: 90, retries: 1, region_priority: "in-first" },
        capabilities
      };
      const resp = await fetch("http://localhost:8000/agents/supervise/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: `HTTP ${resp.status}` }));
        throw new Error(err.detail || `Request failed: ${resp.status}`);
      }
      const data = await resp.json();
      setPlan(data.plan || []);
      setArtifacts(data.artifacts || []);
      setSummary(data.summary || "");
    } catch (e: any) {
      setError(e?.message || "Mission failed");
    } finally {
      setRunning(false);
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold">Supervisor</h2>
      </div>

      <div className="grid md:grid-cols-2 gap-4 mb-4">
        <div>
          <label className="block text-sm font-medium mb-1">Mission Goal</label>
          <input value={goal} onChange={e => setGoal(e.target.value)} className="w-full border-2 border-black rounded p-2" />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Max Steps</label>
          <input type="number" value={maxSteps} onChange={e => setMaxSteps(parseInt(e.target.value || '1'))} className="w-full border-2 border-black rounded p-2" />
        </div>
      </div>

      <div className="mb-4">
        <label className="block text-sm font-medium mb-1">Capabilities</label>
        <div className="flex flex-wrap gap-2">
          {[
            { key: "profile_analyst", label: "Profile Analyst" },
            { key: "supply_hunter", label: "Supply Hunter" },
            { key: "growth_marketer", label: "Growth Marketer" },
            { key: "event_scout", label: "Event Scout" },
          ].map(opt => (
            <label key={opt.key} className="flex items-center gap-2 border-2 border-black rounded px-2 py-1">
              <input type="checkbox" checked={capabilities.includes(opt.key)} onChange={(e) => {
                setCapabilities(prev => e.target.checked ? [...prev, opt.key] : prev.filter(x => x !== opt.key));
              }} />
              <span>{opt.label}</span>
            </label>
          ))}
        </div>
      </div>

      <button onClick={runMission} disabled={running} className="px-4 py-2 bg-black text-white rounded hover:bg-gray-800 disabled:bg-gray-400 mb-4">
        {running ? "Running Mission..." : "Run Supervised Mission"}
      </button>

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
          <h3 className="text-lg font-semibold mb-2">Team Log</h3>
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

      {plan.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-2">Plan ({plan.length} steps)</h3>
          <pre className="text-xs bg-gray-50 p-3 border rounded overflow-auto">{JSON.stringify(plan, null, 2)}</pre>
        </div>
      )}

      {artifacts.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-2">Artifacts ({artifacts.length})</h3>
          <pre className="text-xs bg-gray-50 p-3 border rounded overflow-auto">{JSON.stringify(artifacts, null, 2)}</pre>
        </div>
      )}

      {summary && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-2">Summary</h3>
          <div className="text-sm whitespace-pre-wrap border rounded p-3 bg-gray-50">{summary}</div>
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
      const resp = await fetch("http://localhost:8000/agents/tools");
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
        <h2 className="text-2xl font-bold">Tools</h2>
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
            <details className="mt-2">
              <summary className="cursor-pointer text-sm font-semibold">Schemas</summary>
              <div className="grid md:grid-cols-2 gap-2 mt-2 text-xs">
                <div>
                  <div className="font-semibold">Input</div>
                  <pre className="bg-gray-50 p-2 border rounded overflow-auto">{JSON.stringify(t.input_schema, null, 2)}</pre>
                </div>
                <div>
                  <div className="font-semibold">Output</div>
                  <pre className="bg-gray-50 p-2 border rounded overflow-auto">{JSON.stringify(t.output_schema, null, 2)}</pre>
                </div>
              </div>
            </details>
          </div>
        ))}
        {tools.length === 0 && !loading && !error && (
          <p className="text-gray-600">No tools found.</p>
        )}
      </div>
    </div>
  );
}

function SuppliersView({ answers: propAnswers }: { answers?: Record<string, string> }) {
  const [isSearching, setIsSearching] = React.useState(false);
  const [searchLogs, setSearchLogs] = React.useState<any[]>([]);
  const [suppliers, setSuppliers] = React.useState<any[]>([]);
  const [recentSuppliers, setRecentSuppliers] = React.useState<any[]>([]);
  const [expandedLog, setExpandedLog] = React.useState<number | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [loadingRecent, setLoadingRecent] = React.useState(false);
  const wsRef = React.useRef<WebSocket | null>(null);
  const reconnectTimer = React.useRef<any>(null);

  const connectWebSocket = React.useCallback(() => {
    try {
      const ws = new WebSocket("ws://localhost:8000/ws");
      ws.onopen = () => {
        ws.send(JSON.stringify({ type: "subscribe" }));
      };
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "agent_progress") {
          setSearchLogs(prev => [...prev, {
            timestamp: data.timestamp,
            agent: data.agent,
            step: data.step,
            message: data.message || data.step,
            data: data.data
          }]);
        }
      };
      ws.onerror = () => {
        setError("WebSocket connection lost. Reconnecting...");
      };
      ws.onclose = () => {
        reconnectTimer.current = setTimeout(connectWebSocket, 5000);
      };
      wsRef.current = ws;
    } catch (e) {
      setError("WebSocket init failed");
    }
  }, []);

  const loadRecentSuppliers = React.useCallback(async () => {
    try {
      setLoadingRecent(true);
      const resp = await fetch("http://localhost:8000/agents/suppliers/recent");
      if (resp.ok) {
        const data = await resp.json();
        setRecentSuppliers(Array.isArray(data.results) ? data.results : (data.suppliers || []));
      }
    } catch (e) {
      // ignore
    } finally {
      setLoadingRecent(false);
    }
  }, []);

  React.useEffect(() => {
    connectWebSocket();
    loadRecentSuppliers();
    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [connectWebSocket, loadRecentSuppliers]);

  const startSupplierSearch = async () => {
    setIsSearching(true);
    setSearchLogs([]);
    setSuppliers([]);
    setError(null);

    try {
      // Get user context from props or localStorage
      const answers = propAnswers || JSON.parse(localStorage.getItem("questionnaireAnswers") || "{}");
      
      const suppliesList = (answers.supplies || "").split(",").map((s: string) => s.trim()).filter(Boolean);
      if (suppliesList.length === 0) {
        throw new Error("No supplies specified. Please fill out the questionnaire first.");
      }

      const response = await fetch("http://localhost:8000/agents/supply/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          craft_type: answers.craft_type || "pottery",
          supplies_needed: suppliesList,
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
      setSearchLogs(prev => [...prev, {
        timestamp: new Date().toISOString(),
        agent: "Supply Hunter",
        step: "complete",
        message: `✅ Search complete! Found ${result.total_suppliers_found || 0} suppliers`,
        data: result
      }]);
    } catch (error: any) {
      const errorMessage = error?.message || "Failed to search for suppliers. Please check your backend connection.";
      setError(errorMessage);
      setSearchLogs(prev => [...prev, {
        timestamp: new Date().toISOString(),
        agent: "Supply Hunter",
        step: "error",
        message: `❌ Error: ${errorMessage}`,
        data: { error: errorMessage, stack: error?.stack }
      }]);
      console.error("Search error:", error);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold">Suppliers</h2>
        <button
          onClick={startSupplierSearch}
          disabled={isSearching}
          className="px-4 py-2 bg-black text-white rounded hover:bg-gray-800 disabled:bg-gray-400"
        >
          {isSearching ? "Searching..." : "Search for Suppliers"}
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

      {isSearching && (
        <div className="mb-4 p-4 bg-yellow-50 border-2 border-yellow-200 rounded-lg">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse" />
            <p className="font-semibold text-yellow-800">Searching for suppliers...</p>
          </div>
          <p className="text-sm text-yellow-700 mt-2">Click any log entry below to see details</p>
        </div>
      )}

      {/* Search Logs - Clickable */}
      {searchLogs.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-2">Work Log</h3>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {searchLogs.map((log, idx) => (
              <div
                key={idx}
                onClick={() => setExpandedLog(expandedLog === idx ? null : idx)}
                className={`p-3 border-2 rounded-lg cursor-pointer transition-colors ${
                  expandedLog === idx 
                    ? "border-black bg-gray-50" 
                    : "border-gray-200 hover:border-gray-400"
                }`}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold">{log.agent}</span>
                      <span className="text-xs text-gray-500">{new Date(log.timestamp).toLocaleTimeString()}</span>
                    </div>
                    <p className="text-sm mt-1">{log.message}</p>
                    {expandedLog === idx && (
                      <div className="mt-2 p-2 bg-gray-100 rounded text-xs">
                        <p><strong>Step:</strong> {log.step}</p>
                        <pre className="mt-1 overflow-auto text-xs">
                          {JSON.stringify(log.data, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                  <span className="text-xs text-gray-400">{expandedLog === idx ? "▲" : "▼"}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Suppliers (if any, before searching) */}
      {!isSearching && recentSuppliers.length > 0 && suppliers.length === 0 && (
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-lg font-semibold">Recent Suppliers</h3>
            <button onClick={loadRecentSuppliers} disabled={loadingRecent} className="px-3 py-1 text-sm bg-black text-white rounded hover:bg-gray-800 disabled:bg-gray-400">{loadingRecent ? "Refreshing..." : "Refresh"}</button>
          </div>
          <div className="grid gap-4">
            {recentSuppliers.map((s, idx) => (
              <div key={idx} className="border-2 border-black p-4 rounded-lg">
                <h4 className="font-bold">{s.name || "Unknown Supplier"}</h4>
                {s.location && (
                  <p className="text-sm text-gray-600">📍 {s.location.city}{s.location.state ? ", " + s.location.state : ""}{s.location.country ? ", " + s.location.country : ""}</p>
                )}
                {s.products && Array.isArray(s.products) && (
                  <p className="text-sm mt-1"><strong>Products:</strong> {s.products.join(", ")}</p>
                )}
                {s.contact?.website && (
                  <a href={s.contact.website} target="_blank" rel="noopener noreferrer" className="text-blue-600 text-sm underline">Visit Website</a>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Suppliers Results */}
      {suppliers.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-2">Found Suppliers ({suppliers.length})</h3>
          <div className="grid gap-4">
            {suppliers.map((supplier, idx) => (
              <div key={idx} className="border-2 border-black p-4 rounded-lg">
                <h4 className="font-bold">{supplier.name || "Unknown Supplier"}</h4>
                {supplier.location && (
                  <p className="text-sm text-gray-600">
                    📍 {supplier.location.city}, {supplier.location.state}, {supplier.location.country}
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
                {supplier.contact?.website && (
                  <a href={supplier.contact.website} target="_blank" rel="noopener noreferrer" className="text-blue-600 text-sm underline">
                    Visit Website
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {!isSearching && searchLogs.length === 0 && suppliers.length === 0 && (
        <p className="text-gray-600">Click "Search for Suppliers" to begin</p>
      )}
    </div>
  );
}

// Reusable Agent View Component
function AgentView({
  title,
  endpoint,
  buttonText,
  answers,
  requestBuilder
}: {
  title: string;
  endpoint: string;
  buttonText: string;
  answers?: Record<string, string>;
  requestBuilder: (answers: Record<string, string>) => any;
}) {
  const [isSearching, setIsSearching] = React.useState(false);
  const [searchLogs, setSearchLogs] = React.useState<any[]>([]);
  const [results, setResults] = React.useState<any[]>([]);
  const [recentResults, setRecentResults] = React.useState<any[]>([]);
  const [loadingRecent, setLoadingRecent] = React.useState(false);
  const [expandedLog, setExpandedLog] = React.useState<number | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const wsRef = React.useRef<WebSocket | null>(null);
  const reconnectTimer = React.useRef<any>(null);

  const connectWebSocket = React.useCallback(() => {
    try {
      const ws = new WebSocket("ws://localhost:8000/ws");
      ws.onopen = () => {
        ws.send(JSON.stringify({ type: "subscribe" }));
      };
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "agent_progress") {
          setSearchLogs(prev => [...prev, {
            timestamp: data.timestamp,
            agent: data.agent,
            step: data.step,
            message: data.message || data.step,
            data: data.data
          }]);
        }
      };
      ws.onerror = () => setError("WebSocket connection lost. Reconnecting...");
      ws.onclose = () => {
        reconnectTimer.current = setTimeout(connectWebSocket, 5000);
      };
      wsRef.current = ws;
    } catch (e) {
      setError("WebSocket init failed");
    }
  }, []);

  const loadRecent = React.useCallback(async () => {
    try {
      setLoadingRecent(true);
      let url: string | null = null;
      if (endpoint === "growth/analyze") url = "http://localhost:8000/agents/opportunities/recent";
      else if (endpoint === "events/search") url = "http://localhost:8000/agents/events/recent";
      else if (endpoint === "supply/search") url = "http://localhost:8000/agents/materials/recent";
      if (!url) return;
      const resp = await fetch(url);
      if (resp.ok) {
        const data = await resp.json();
        const arr = data.results || data.events || data.opportunities || data.materials || [];
        setRecentResults(Array.isArray(arr) ? arr : []);
      }
    } catch (e) {
      // ignore
    } finally {
      setLoadingRecent(false);
    }
  }, [endpoint]);

  React.useEffect(() => {
    connectWebSocket();
    loadRecent();
    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [connectWebSocket, loadRecent]);

  const startSearch = async () => {
    setIsSearching(true);
    setSearchLogs([]);
    setResults([]);
    setError(null);

    try {
      const userAnswers = answers || JSON.parse(localStorage.getItem("questionnaireAnswers") || "{}");
      const requestBody = requestBuilder(userAnswers);

      const response = await fetch(`http://localhost:8000/agents/${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `HTTP ${response.status}: ${response.statusText}` }));
        throw new Error(errorData.detail || `Request failed: ${response.status}`);
      }

      const result = await response.json();
      const resultsArray = result.results || result.events || result.opportunities || result.materials || [];
      setResults(resultsArray);
      setSearchLogs(prev => [...prev, {
        timestamp: new Date().toISOString(),
        agent: title,
        step: "complete",
        message: `✅ Complete! Found ${resultsArray.length} items`,
        data: result
      }]);
    } catch (error: any) {
      const errorMessage = error?.message || `Failed to ${buttonText.toLowerCase()}`;
      setError(errorMessage);
      setSearchLogs(prev => [...prev, {
        timestamp: new Date().toISOString(),
        agent: title,
        step: "error",
        message: `❌ Error: ${errorMessage}`,
        data: { error: errorMessage }
      }]);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold">{title}</h2>
        <button
          onClick={startSearch}
          disabled={isSearching}
          className="px-4 py-2 bg-black text-white rounded hover:bg-gray-800 disabled:bg-gray-400"
        >
          {isSearching ? "Searching..." : buttonText}
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

      {!isSearching && recentResults.length > 0 && results.length === 0 && (
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-lg font-semibold">Recent</h3>
            <button onClick={loadRecent} disabled={loadingRecent} className="px-3 py-1 text-sm bg-black text-white rounded hover:bg-gray-800 disabled:bg-gray-400">{loadingRecent ? "Refreshing..." : "Refresh"}</button>
          </div>
          <pre className="text-xs bg-gray-50 p-3 border rounded overflow-auto">{JSON.stringify(recentResults, null, 2)}</pre>
        </div>
      )}

      {isSearching && (
        <div className="mb-4 p-4 bg-yellow-50 border-2 border-yellow-200 rounded-lg">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse" />
            <p className="font-semibold text-yellow-800">{buttonText}...</p>
          </div>
          <p className="text-sm text-yellow-700 mt-2">Click any log entry below to see details</p>
        </div>
      )}

      {searchLogs.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-2">Work Log</h3>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {searchLogs.map((log, idx) => (
              <div
                key={idx}
                onClick={() => setExpandedLog(expandedLog === idx ? null : idx)}
                className={`p-3 border-2 rounded-lg cursor-pointer transition-colors ${
                  expandedLog === idx ? "border-black bg-gray-50" : "border-gray-200 hover:border-gray-400"
                }`}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold">{log.agent}</span>
                      <span className="text-xs text-gray-500">{new Date(log.timestamp).toLocaleTimeString()}</span>
                    </div>
                    <p className="text-sm mt-1">{log.message}</p>
                    {expandedLog === idx && (
                      <div className="mt-2 p-2 bg-gray-100 rounded text-xs">
                        <p><strong>Step:</strong> {log.step}</p>
                        <pre className="mt-1 overflow-auto text-xs">{JSON.stringify(log.data, null, 2)}</pre>
                      </div>
                    )}
                  </div>
                  <span className="text-xs text-gray-400">{expandedLog === idx ? "▲" : "▼"}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {results.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-2">Results ({results.length})</h3>
          <div className="grid gap-4">
            {results.map((item: any, idx: number) => (
              <div key={idx} className="border-2 border-black p-4 rounded-lg">
                <h4 className="font-bold">{item.name || item.title || `Item ${idx + 1}`}</h4>
                {item.description && <p className="text-sm mt-1">{item.description}</p>}
                {item.location && (
                  <p className="text-sm text-gray-600">
                    📍 {item.location.city || item.location}, {item.location.state || ""}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {!isSearching && searchLogs.length === 0 && results.length === 0 && (
        <p className="text-gray-600">Click "{buttonText}" to begin</p>
      )}
    </div>
  );
}

function OpportunitiesView({ answers }: { answers?: Record<string, string> }) {
  return (
    <AgentView
      title="Opportunities"
      endpoint="growth/analyze"
      buttonText="Analyze Opportunities"
      answers={answers}
      requestBuilder={(ans) => ({
        craft_type: ans.craft_type || "pottery",
        specialization: ans.tradition || "",
        current_products: (ans.products || "").split(",").map((s: string) => s.trim()).filter(Boolean),
        location: {
          city: ans.location?.split(",")[0] || "Jaipur",
          state: ans.location?.split(",")[1] || "Rajasthan"
        }
      })}
    />
  );
}

function GrowthMarketerView({ answers }: { answers?: Record<string, string> }) {
  return (
    <AgentView
      title="Growth Marketer"
      endpoint="growth/analyze"
      buttonText="Analyze Growth"
      answers={answers}
      requestBuilder={(ans) => ({
        craft_type: ans.craft_type || "pottery",
        specialization: ans.tradition || "",
        current_products: (ans.products || "").split(",").map((s: string) => s.trim()).filter(Boolean),
        location: {
          city: ans.location?.split(",")[0] || "Jaipur",
          state: ans.location?.split(",")[1] || "Rajasthan"
        }
      })}
    />
  );
}

function EventsView({ answers }: { answers?: Record<string, string> }) {
  const [city, setCity] = React.useState("");
  const [dateFrom, setDateFrom] = React.useState("");
  const [dateTo, setDateTo] = React.useState("");
  const [recent, setRecent] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const loadRecent = React.useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const params = new URLSearchParams();
      if (city) params.set("city", city);
      if (dateFrom) params.set("date_from", dateFrom);
      if (dateTo) params.set("date_to", dateTo);
      const url = `http://localhost:8000/agents/events/recent${params.toString() ? `?${params.toString()}` : ""}`;
      const resp = await fetch(url);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      setRecent(data.results || data.events || []);
    } catch (e: any) {
      setError(e?.message || "Failed to load recent events");
    } finally {
      setLoading(false);
    }
  }, [city, dateFrom, dateTo]);

  return (
    <div className="space-y-6">
      <div className="border-2 border-black p-4 rounded">
        <div className="flex flex-col md:flex-row gap-3 md:items-end">
          <div className="flex-1">
            <label className="text-xs font-semibold">City</label>
            <input className="w-full border border-gray-300 rounded p-2 text-sm" placeholder="e.g. Jaipur" value={city} onChange={(e) => setCity(e.target.value)} />
          </div>
          <div>
            <label className="text-xs font-semibold">From (YYYY-MM-DD)</label>
            <input className="border border-gray-300 rounded p-2 text-sm" placeholder="YYYY-MM-DD" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
          </div>
          <div>
            <label className="text-xs font-semibold">To (YYYY-MM-DD)</label>
            <input className="border border-gray-300 rounded p-2 text-sm" placeholder="YYYY-MM-DD" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
          </div>
          <button onClick={loadRecent} disabled={loading} className="px-3 py-2 bg-black text-white rounded hover:bg-gray-800 disabled:bg-gray-400">{loading ? "Loading..." : "Load Recent"}</button>
        </div>
        {error && (
          <div className="mt-2 p-2 bg-red-50 border-2 border-red-500 rounded"><p className="text-sm text-red-800 font-semibold">Error: {error}</p></div>
        )}
        {recent.length > 0 && (
          <div className="mt-3">
            <h3 className="text-lg font-semibold">Recent Events</h3>
            <pre className="text-xs bg-gray-50 p-3 border rounded overflow-auto">{JSON.stringify(recent, null, 2)}</pre>
          </div>
        )}
      </div>
      <AgentView
        title="Events"
        endpoint="events/search"
        buttonText="Find Events"
        answers={answers}
        requestBuilder={(ans) => ({
          craft_type: ans.craft_type || "pottery",
          location: {
            city: ans.location?.split(",")[0] || "Jaipur",
            state: ans.location?.split(",")[1] || "Rajasthan"
          },
          travel_radius_km: 100
        })}
      />
    </div>
  );
}

function MaterialsView({ answers }: { answers?: Record<string, string> }) {
  return (
    <AgentView
      title="Materials & Equipment"
      endpoint="supply/search"
      buttonText="Find Materials"
      answers={answers}
      requestBuilder={(ans) => ({
        craft_type: ans.craft_type || "pottery",
        supplies_needed: (ans.supplies || "").split(",").map((s: string) => s.trim()).filter(Boolean),
        location: {
          city: ans.location?.split(",")[0] || "Jaipur",
          state: ans.location?.split(",")[1] || "Rajasthan"
        }
      })}
    />
  );
}

function ContextView({ answers }: { answers: Record<string, string> }) {
  const [notes, setNotes] = React.useState("");
  const [loading, setLoading] = React.useState(false);
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const loadContext = React.useCallback(async () => {
    try {
      setLoading(true);
      const resp = await fetch("http://localhost:8000/context");
      if (resp.ok) {
        const data = await resp.json();
        const s = (data?.context?.notes as string) || "";
        setNotes(s);
      }
    } catch (e: any) {
      setError(e?.message || "Failed to load context");
    } finally {
      setLoading(false);
    }
  }, []);

  const saveContext = React.useCallback(async () => {
    try {
      setSaving(true);
      setError(null);
      const resp = await fetch("http://localhost:8000/context", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ context: { notes } })
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${resp.status}`);
      }
    } catch (e: any) {
      setError(e?.message || "Failed to save context");
    } finally {
      setSaving(false);
    }
  }, [notes]);

  React.useEffect(() => { loadContext(); }, [loadContext]);

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Context</h2>
      {error && (
        <div className="mb-4 p-3 bg-red-50 border-2 border-red-500 rounded-lg">
          <p className="font-semibold text-red-800">Error: {error}</p>
        </div>
      )}
      <div className="grid gap-4">
        <div className="border border-black p-4 rounded">
          <h3 className="font-semibold mb-2">Questionnaire</h3>
          <div className="grid md:grid-cols-2 gap-3 text-sm">
            {Object.entries(answers).map(([key, value]) => (
              <div key={key}>
                <div className="font-semibold capitalize">{key.replace("_", " ")}</div>
                <div className="text-gray-600">{value}</div>
              </div>
            ))}
          </div>
        </div>
        <div className="border border-black p-4 rounded">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold">Notes</h3>
            <button onClick={saveContext} disabled={saving} className="px-3 py-1 text-sm bg-black text-white rounded hover:bg-gray-800 disabled:bg-gray-400">{saving ? "Saving..." : "Save"}</button>
          </div>
          <textarea
            className="w-full border border-gray-300 rounded mt-2 p-2 text-sm"
            rows={8}
            placeholder={loading ? "Loading..." : "Add any additional context here..."}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
        </div>
      </div>
    </div>
  );
}

function SettingsView() {
  const [flightCheck, setFlightCheck] = React.useState<any>(null);
  const [loading, setLoading] = React.useState(false);

  // Auto-load flight check on mount
  React.useEffect(() => {
    runFlightCheck();
  }, []);

  const runFlightCheck = async () => {
    setLoading(true);
    try {
      const response = await fetch("http://localhost:8000/health/flight-check");
      if (!response.ok) {
        // Try to parse error response, but still show structure
        const errorData = await response.json().catch(() => null);
        setFlightCheck({
          overall_status: "error",
          timestamp: new Date().toISOString(),
          checks: errorData?.checks || {},
          errors: [{
            component: "flight_check",
            status: "error",
            message: errorData?.message || `HTTP ${response.status}: ${response.statusText}`,
            details: { error: `HTTP ${response.status}`, statusText: response.statusText }
          }, ...(errorData?.errors || [])]
        });
        return;
      }
      const data = await response.json();
      setFlightCheck(data);
    } catch (error: any) {
      console.error("Flight check error:", error);
      // Even on network error, show structure with unknown statuses
      setFlightCheck({
        overall_status: "error",
        timestamp: new Date().toISOString(),
        checks: {
          ollama: {
            status: "unknown",
            message: "Connection failed - backend may not be running",
            details: { error: "Network error", url: "http://localhost:8000/health/flight-check" }
          },
          ollama_generation: {
            status: "unknown",
            message: "Cannot test - backend unreachable",
            details: { error: error?.message || "Failed to fetch" }
          },
          chromadb: {
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
          message: error?.message || "Failed to connect to backend. Is the server running on http://localhost:8000?",
          details: { 
            error: String(error),
            suggestion: "Make sure the backend server is running: python -m uvicorn backend.main:app --reload"
          }
        }]
      });
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "healthy": return "bg-green-100 border-green-500 text-green-800";
      case "unhealthy": return "bg-red-100 border-red-500 text-red-800";
      case "warning": return "bg-yellow-100 border-yellow-500 text-yellow-800";
      case "degraded": return "bg-orange-100 border-orange-500 text-orange-800";
      default: return "bg-gray-100 border-gray-500 text-gray-800";
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold">Settings & Flight Check</h2>
        <p className="text-sm text-gray-600">Flight check runs automatically on page load</p>
      </div>

      {flightCheck && (
        <div className="space-y-4">
          <div className={`p-4 border-2 rounded-lg ${getStatusColor(flightCheck.overall_status)}`}>
            <div className="flex justify-between items-center mb-2">
              <div>
                <h3 className="font-bold text-lg">
                  Overall Status: {flightCheck.overall_status.toUpperCase()}
                </h3>
                {flightCheck.timestamp && (
                  <p className="text-sm mt-1">{new Date(flightCheck.timestamp).toLocaleString()}</p>
                )}
              </div>
              <button
                onClick={runFlightCheck}
                disabled={loading}
                className="px-3 py-1 text-sm bg-black text-white rounded hover:bg-gray-800 disabled:bg-gray-400"
              >
                {loading ? "Refreshing..." : "Refresh"}
              </button>
            </div>
          </div>

          {flightCheck.errors && flightCheck.errors.length > 0 && (
            <div className="p-4 bg-red-50 border-2 border-red-500 rounded-lg">
              <h3 className="font-bold text-red-800 mb-2">⚠️ Errors Found:</h3>
              {flightCheck.errors.map((err: any, idx: number) => (
                <div key={idx} className="mb-2 p-2 bg-red-100 rounded">
                  <p className="font-semibold text-red-800">{err.component}: {err.message}</p>
                  {err.details && Object.keys(err.details).length > 0 && (
                    <pre className="text-xs mt-1 text-red-700">
                      {JSON.stringify(err.details, null, 2)}
                    </pre>
                  )}
                </div>
              ))}
            </div>
          )}

          <div className="space-y-3">
            <h3 className="font-semibold text-lg">System Checks:</h3>
            {Object.keys(flightCheck.checks || {}).length === 0 ? (
              <p className="text-gray-600">No checks available</p>
            ) : (
              Object.entries(flightCheck.checks || {}).map(([key, check]: [string, any]) => {
                // Skip duplicate serpapi entry if tavily exists
                if (key === "serpapi" && flightCheck.checks?.tavily) {
                  return null;
                }
                
                const statusDisplay = check.status === "healthy" ? "✅ PASS" : 
                                     check.status === "unhealthy" ? "❌ FAIL" :
                                     check.status === "warning" ? "⚠️ WARNING" :
                                     check.status === "degraded" ? "⚠️ DEGRADED" : "❓ UNKNOWN";
                
                return (
                  <div
                    key={key}
                    className={`p-4 border-2 rounded-lg ${getStatusColor(check.status)}`}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex-1">
                        <h4 className="font-semibold capitalize text-lg">
                          {key.replace("_", " ").split(" ").map((w: string) => 
                            w.charAt(0).toUpperCase() + w.slice(1)
                          ).join(" ")}
                        </h4>
                        <p className="text-sm mt-1">{check.message || "No message"}</p>
                      </div>
                      <div className="ml-4 text-right">
                        <span className="text-sm font-bold block">{statusDisplay}</span>
                        <span className="text-xs text-gray-600">{check.status}</span>
                      </div>
                    </div>
                    {check.details && Object.keys(check.details).length > 0 && (
                      <div className="mt-2 text-xs bg-white bg-opacity-50 p-2 rounded">
                        <details>
                          <summary className="cursor-pointer font-semibold mb-1">Show Details</summary>
                          <pre className="whitespace-pre-wrap mt-1">
                            {JSON.stringify(check.details, null, 2)}
                          </pre>
                        </details>
                      </div>
                    )}
                  </div>
                );
              }).filter(Boolean)
            )}
          </div>
        </div>
      )}

      {loading && !flightCheck && (
        <div className="text-center py-8">
          <p className="text-gray-600">Running flight check...</p>
        </div>
      )}

      {!loading && !flightCheck && (
        <div className="text-center py-8">
          <p className="text-gray-600 mb-4">Loading flight check...</p>
        </div>
      )}
    </div>
  );
}


