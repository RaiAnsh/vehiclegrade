"use client";

import { useState } from "react";

import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { parseListingText } from "@/lib/api";
import { ParsedListing } from "@/lib/types";

interface PasteTextFormProps {
  onParsed: (parsed: ParsedListing) => void;
}

export function PasteTextForm({ onParsed }: PasteTextFormProps) {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleParse() {
    setLoading(true);
    setError(null);
    parseListingText(text)
      .then((parsed) => onParsed(parsed))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }

  return (
    <Card className="p-6">
      <label className="mb-1.5 block text-xs text-muted">Paste the listing description</label>
      <textarea
        className="w-full rounded-xl bg-white/[0.04] border border-white/10 px-4 py-2.5 text-sm text-foreground placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/50 transition-colors"
        rows={8}
        placeholder={`e.g. "2017 BMW 3-Series 340i, 104,000 km, clean title, automatic, $14,500 obo. Located in Hamilton."`}
        value={text}
        onChange={(e) => setText(e.target.value)}
      />

      <p className="mt-2 text-xs text-muted">
        We extract year, make, model, price, mileage, title status, transmission, fuel type, and location with simple
        pattern matching first. If a field is still missing and AI assistance is available, it may fill in the rest
        (marked &ldquo;AI-assisted&rdquo;) &mdash; always review the prefilled form before analyzing.
      </p>

      {error && <p className="mt-3 text-sm text-[var(--avoid)]">{error}</p>}

      <div className="mt-4 flex justify-end">
        <Button onClick={handleParse} disabled={!text.trim() || loading}>
          {loading ? "Parsing..." : "Parse Listing"}
        </Button>
      </div>
    </Card>
  );
}
