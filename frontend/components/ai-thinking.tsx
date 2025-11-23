"use client";

import React from "react";
import { TextShimmer } from "@/components/ui/text-shimmer";

interface AISearchActivity {
  agent: string;
  action: string;
  message?: string;
  step?: string;
  url?: string;
  query?: string;
  data?: any;
  timestamp?: string;
  status: "thinking" | "searching" | "analyzing" | "scraping" | "complete";
}

interface AIThinkingProps {
  activities: AISearchActivity[];
}

export function AIThinking({ activities }: AIThinkingProps) {
  const [expandedActivity, setExpandedActivity] = React.useState<number | null>(null);

  if (activities.length === 0) return null;

  const currentActivity = activities[activities.length - 1];

  return (
    <div className="fixed bottom-4 right-4 bg-white border-2 border-black rounded-lg shadow-lg p-4 max-w-md z-50 max-h-[600px] overflow-y-auto">
      <div className="flex items-center gap-2 mb-2">
        <div className="w-2 h-2 bg-black rounded-full animate-pulse" />
        <TextShimmer className="text-sm font-semibold">
          {`AI Agent: ${currentActivity.agent}`}
        </TextShimmer>
      </div>

      <div className="space-y-2 mb-3">
        <p className="text-xs text-gray-600">
          <strong>Current:</strong> {currentActivity.message || currentActivity.action}
        </p>
        
        {currentActivity.timestamp && (
          <p className="text-xs text-gray-400">
            {new Date(currentActivity.timestamp).toLocaleTimeString()}
          </p>
        )}
      </div>

      {activities.length > 1 && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <p className="text-xs font-semibold text-gray-700 mb-2">
            Activity Log ({activities.length} steps) - Click to expand
          </p>
          <div className="mt-1 space-y-1 max-h-64 overflow-y-auto">
            {activities.map((activity, idx) => (
              <div
                key={idx}
                onClick={() => setExpandedActivity(expandedActivity === idx ? null : idx)}
                className={`text-xs p-2 rounded cursor-pointer transition-colors ${
                  expandedActivity === idx
                    ? "bg-gray-100 border border-gray-300"
                    : "hover:bg-gray-50"
                }`}
              >
                <div className="flex items-center gap-1 mb-1">
                  <div className="w-1 h-1 bg-gray-400 rounded-full" />
                  <span className="font-semibold">{activity.agent}:</span>
                  <span className="text-gray-600">{activity.message || activity.action}</span>
                  {activity.timestamp && (
                    <span className="text-gray-400 ml-auto">
                      {new Date(activity.timestamp).toLocaleTimeString()}
                    </span>
                  )}
                </div>
                {expandedActivity === idx && activity.data && (
                  <div className="mt-2 pl-3 border-l-2 border-gray-300">
                    <p className="text-xs text-gray-500 mb-1">
                      <strong>Step:</strong> {activity.step}
                    </p>
                    <pre className="text-xs bg-gray-50 p-2 rounded overflow-auto max-h-32">
                      {JSON.stringify(activity.data, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

