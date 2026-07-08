"use client";

import { useState } from "react";

import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Negotiation } from "@/lib/types";

interface NegotiationAssistantProps {
  negotiation: Negotiation;
}

export function NegotiationAssistant({ negotiation }: NegotiationAssistantProps) {
  const [copied, setCopied] = useState(false);

  function handleCopy() {
    navigator.clipboard.writeText(negotiation.message).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <Card className="p-6">
      <h2 className="text-lg font-medium">Negotiation Assistant</h2>

      <div className="mt-4">
        <p className="text-xs text-muted">Suggested opening offer</p>
        <p className="mt-1 text-2xl font-semibold">${negotiation.suggested_offer.toLocaleString()}</p>
        <p className="mt-2 text-sm text-muted">{negotiation.reasoning}</p>
      </div>

      <div className="mt-5 border-t border-white/5 pt-4">
        <div className="flex items-center justify-between">
          <p className="text-xs text-muted">Ready-to-send message</p>
          <Button variant="ghost" onClick={handleCopy} className="!px-3 !py-1 text-xs">
            {copied ? "Copied!" : "Copy"}
          </Button>
        </div>
        <p className="mt-2 rounded-xl bg-white/[0.03] p-4 text-sm leading-relaxed">{negotiation.message}</p>
      </div>
    </Card>
  );
}
