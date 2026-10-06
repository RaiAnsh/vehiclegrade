"use client";

import { useSearchParams } from "next/navigation";
import { useState } from "react";

import { CalculatorPrefill, FlipCalculator } from "@/components/flip/FlipCalculator";
import { FlipResearch } from "@/components/flip/FlipResearch";
import { FlipRoadmap } from "@/components/flip/FlipRoadmap";
import { MyFlips } from "@/components/flip/MyFlips";
import { Tabs } from "@/components/ui/Tabs";
import { useFlipLedger } from "@/hooks/useFlipLedger";
import { Condition, TitleStatus } from "@/lib/types";

type Tab = "roadmap" | "research" | "calculator" | "flips";

// Links from other pages (e.g. a dashboard deal card) arrive as /flip?make=...&price=...
function prefillFromQuery(params: URLSearchParams): CalculatorPrefill | undefined {
  const make = params.get("make");
  const model = params.get("model");
  if (!make || !model) return undefined;
  const num = (key: string) => {
    const n = Number(params.get(key));
    return params.get(key) && Number.isFinite(n) && n > 0 ? n : undefined;
  };
  return {
    make, model, year: num("year"), trim: params.get("trim") ?? undefined,
    mileage_km: num("mileage"), purchase_price: num("price"),
    title_status: (params.get("title") as TitleStatus) ?? undefined,
    condition: (params.get("condition") as Condition) ?? undefined,
  };
}

export function FlipHub() {
  const ledger = useFlipLedger();
  const searchParams = useSearchParams();
  const initialPrefill = prefillFromQuery(searchParams);
  const [tab, setTab] = useState<Tab>(initialPrefill ? "calculator" : "roadmap");
  // Bumping the key remounts the calculator so a new prefill actually applies.
  const [prefill, setPrefill] = useState<CalculatorPrefill | undefined>(initialPrefill);
  const [calculatorKey, setCalculatorKey] = useState(0);

  function runNumbers(next: CalculatorPrefill) {
    setPrefill(next);
    setCalculatorKey((k) => k + 1);
    setTab("calculator");
  }

  return (
    <div className="space-y-6">
      <Tabs
        tabs={[
          { value: "roadmap", label: "Roadmap" },
          { value: "research", label: "Research a car" },
          { value: "calculator", label: "Calculator" },
          { value: "flips", label: "My flips", count: ledger.flips.length || undefined },
        ]}
        active={tab}
        onChange={(v) => setTab(v as Tab)}
      />

      {tab === "roadmap" && <FlipRoadmap ledger={ledger} onRunNumbers={runNumbers} />}
      {tab === "research" && <FlipResearch onRunNumbers={runNumbers} />}
      {tab === "calculator" && (
        <FlipCalculator
          key={calculatorKey}
          prefill={prefill}
          onTrack={(flip) => {
            ledger.addFlip(flip);
          }}
        />
      )}
      {tab === "flips" && <MyFlips ledger={ledger} goToCalculator={() => setTab("calculator")} />}
    </div>
  );
}
