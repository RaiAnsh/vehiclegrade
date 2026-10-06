"use client";

import { useState } from "react";

import { CalculatorPrefill, FlipCalculator } from "@/components/flip/FlipCalculator";
import { FlipResearch } from "@/components/flip/FlipResearch";
import { FlipRoadmap } from "@/components/flip/FlipRoadmap";
import { MyFlips } from "@/components/flip/MyFlips";
import { Tabs } from "@/components/ui/Tabs";
import { useFlipLedger } from "@/hooks/useFlipLedger";

type Tab = "roadmap" | "research" | "calculator" | "flips";

export function FlipHub() {
  const ledger = useFlipLedger();
  const [tab, setTab] = useState<Tab>("roadmap");
  // Bumping the key remounts the calculator so a new prefill actually applies.
  const [prefill, setPrefill] = useState<CalculatorPrefill | undefined>();
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
