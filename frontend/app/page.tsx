"use client";

import React, { useState, useEffect, useRef } from "react";
import { Questionnaire } from "@/components/questionnaire";
import { ProductionGate } from "@/components/production-gate";
import { AIThinking } from "@/components/ai-thinking";
import { buildApiUrl, buildWsUrl } from "@/lib/config";

export default function Home() {
  const [showQuestionnaire, setShowQuestionnaire] = useState(true);
  const [showProductionGate, setShowProductionGate] = useState(false);
  const [questionnaireAnswers, setQuestionnaireAnswers] = useState<Record<string, string> | null>(null);
  const [aiActivities, setAiActivities] = useState<any[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  const handleQuestionnaireComplete = (answers: Record<string, string>) => {
    setQuestionnaireAnswers(answers);
    setShowQuestionnaire(false);
    setShowProductionGate(true);
    
    // Save to localStorage for later use
    localStorage.setItem("questionnaireAnswers", JSON.stringify(answers));
    
    // Send answers to backend
    fetch(buildApiUrl("/agents/profile-analyst"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        input_text: Object.values(answers).join(" ")
      })
    }).catch(console.error);

    // Connect to WebSocket for real-time updates
    connectWebSocket();
  };

  const connectWebSocket = () => {
    try {
      const ws = new WebSocket(buildWsUrl("/ws"));
      
      ws.onopen = () => {
        console.log("WebSocket connected");
        ws.send(JSON.stringify({ type: "subscribe" }));
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === "agent_progress") {
          setAiActivities(prev => [...prev, {
            agent: data.agent,
            action: data.message || data.step,
            message: data.message || data.step,
            step: data.step,
            status: "thinking",
            data: data.data,
            timestamp: data.timestamp
          }]);
        } else if (data.type === "search_complete" || data.type === "search_progress") {
          setAiActivities(prev => [...prev, {
            agent: "Search Engine",
            action: `Found ${data.results_count || 0} results`,
            message: `Found ${data.results_count || 0} results for: ${data.query}`,
            query: data.query,
            url: data.url,
            status: data.status || "complete",
            timestamp: data.timestamp
          }]);
        } else if (data.type === "scraping_progress") {
          setAiActivities(prev => [...prev, {
            agent: "Web Scraper",
            action: `Scraping with ${data.method || "beautifulsoup"}`,
            message: `Scraping: ${data.url}`,
            url: data.url,
            status: data.status || "scraping",
            timestamp: data.timestamp
          }]);
        }
      };
      
      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
      };
      
      ws.onclose = () => {
        console.log("WebSocket disconnected");
      };
      
      wsRef.current = ws;
    } catch (error) {
      console.error("Failed to connect WebSocket:", error);
    }
  };

  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  return (
    <main className="min-h-screen bg-white">
      {showQuestionnaire && (
        <Questionnaire onComplete={handleQuestionnaireComplete} />
      )}
      
      {showProductionGate && questionnaireAnswers && (
        <ProductionGate initialAnswers={questionnaireAnswers} />
      )}
      
      <AIThinking activities={aiActivities} />
    </main>
  );
}

