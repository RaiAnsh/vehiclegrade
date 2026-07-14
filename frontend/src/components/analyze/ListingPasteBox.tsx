"use client";

import { useState } from "react";
import { motion } from "framer-motion";

import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

interface ListingPasteBoxProps {
  onSubmit: (text: string) => void;
  onEnterManually: () => void;
  loading: boolean;
  error: string | null;
  compact?: boolean;
}

const EXAMPLE_LISTING = `2018 Honda Civic EX
82,000 km
Automatic
$19,500
Clean title
Hamilton

Well maintained. New brakes. Selling because I bought an SUV.`;

export function ListingPasteBox({ onSubmit, onEnterManually, loading, error, compact }: ListingPasteBoxProps) {
  const [text, setText] = useState("");
  const [focused, setFocused] = useState(false);

  const showOverlay = !focused && !text;

  return (
    <Card className={compact ? "p-4" : "p-6"}>
      <div className="relative">
        <textarea
          className={`w-full resize-none rounded-xl bg-white/[0.04] border border-white/10 px-4 py-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/50 transition-colors ${
            compact ? "min-h-[140px]" : "min-h-[220px]"
          }`}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(text.length > 0)}
        />
        {showOverlay && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 1.2 }}
            className="pointer-events-none absolute inset-0 whitespace-pre-line px-4 py-3 text-sm text-muted"
          >
            {EXAMPLE_LISTING}
          </motion.div>
        )}
      </div>

      {error && <p className="mt-3 text-sm text-[var(--avoid)]">{error}</p>}

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
        <button
          type="button"
          onClick={onEnterManually}
          className="text-xs text-muted underline-offset-4 hover:text-foreground hover:underline"
        >
          Don&rsquo;t have a listing? Enter manually
        </button>
        <Button onClick={() => onSubmit(text)} disabled={!text.trim() || loading}>
          {loading ? "Reading listing..." : "Research Vehicle"}
        </Button>
      </div>
    </Card>
  );
}
