"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";

import { Card } from "@/components/ui/Card";

interface AnalyzingProgressProps {
  // True once the real analyzeListing() response has arrived - fast-forwards
  // any remaining steps to checked instead of waiting out the full timer.
  done: boolean;
  // Fired once every step has been checked off (only reachable after `done`
  // is true) - the caller uses this to time revealing the actual result.
  onComplete?: () => void;
  compact?: boolean;
}

const STEPS = [
  "Finding vehicle...",
  "Matching engine...",
  "Checking maintenance...",
  "Searching known issues...",
  "Calculating market value...",
  "Generating report...",
];

const STEP_INTERVAL_MS = 550;
const FAST_FORWARD_STAGGER_MS = 80;

export function AnalyzingProgress({ done, onComplete, compact }: AnalyzingProgressProps) {
  const [checked, setChecked] = useState(0);

  useEffect(() => {
    if (checked >= STEPS.length) {
      if (done) onComplete?.();
      return;
    }
    // Holds on the last step (rather than auto-completing it) until the real
    // response arrives, so the animation never claims to be done before the
    // actual network call is - it just pulses in place if the call is slow.
    if (!done && checked >= STEPS.length - 1) return;
    const delay = done ? FAST_FORWARD_STAGGER_MS : STEP_INTERVAL_MS;
    const timer = setTimeout(() => setChecked((c) => c + 1), delay);
    return () => clearTimeout(timer);
  }, [checked, done, onComplete]);

  return (
    <Card className={compact ? "p-4" : "p-6"}>
      <ul className="space-y-3">
        {STEPS.map((step, i) => {
          const isChecked = i < checked;
          const isActive = i === checked;
          return (
            <li key={step} className="flex items-center gap-3 text-sm">
              <span
                className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[11px] transition-colors duration-300 ${
                  isChecked ? "bg-[var(--good)]/20 text-[var(--good)]" : "bg-white/[0.06] text-muted"
                }`}
              >
                {isChecked ? (
                  <motion.span
                    initial={{ scale: 0.5, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ duration: 0.35, type: "spring", damping: 24, stiffness: 260 }}
                  >
                    ✓
                  </motion.span>
                ) : (
                  <span className={isActive && !done ? "animate-pulse" : ""}>•</span>
                )}
              </span>
              <span className={isChecked ? "text-foreground" : "text-muted"}>{step}</span>
            </li>
          );
        })}
      </ul>
    </Card>
  );
}
