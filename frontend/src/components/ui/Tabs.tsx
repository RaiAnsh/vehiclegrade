"use client";

import clsx from "clsx";

interface Tab {
  value: string;
  label: string;
  count?: number;
}

interface TabsProps {
  tabs: Tab[];
  active: string;
  onChange: (value: string) => void;
}

export function Tabs({ tabs, active, onChange }: TabsProps) {
  return (
    <div className="flex flex-wrap gap-2 border-b border-white/10 pb-px">
      {tabs.map((tab) => {
        const isActive = tab.value === active;
        return (
          <button
            key={tab.value}
            onClick={() => onChange(tab.value)}
            className={clsx(
              "relative flex items-center gap-2 rounded-t-lg px-4 py-2.5 text-sm font-medium transition-colors",
              isActive ? "text-foreground" : "text-muted hover:text-foreground"
            )}
          >
            {tab.label}
            {tab.count !== undefined && (
              <span
                className={clsx(
                  "rounded-full px-1.5 py-0.5 text-xs",
                  isActive ? "bg-[var(--accent)]/20 text-[var(--accent)]" : "bg-white/[0.06] text-muted"
                )}
              >
                {tab.count}
              </span>
            )}
            {isActive && <span className="absolute inset-x-0 -bottom-px h-0.5 rounded-full bg-[var(--accent)]" />}
          </button>
        );
      })}
    </div>
  );
}
