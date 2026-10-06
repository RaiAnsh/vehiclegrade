"use client";

import { useEffect, useState } from "react";
import clsx from "clsx";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { FlipLedger } from "@/hooks/useFlipLedger";
import { getFlipRoadmap } from "@/lib/api";
import { RoadmapLevel } from "@/lib/types";
import { CalculatorPrefill } from "@/components/flip/FlipCalculator";

const money = (n: number | null) => (n === null ? "-" : `${n < 0 ? "-" : ""}$${Math.abs(Math.round(n)).toLocaleString()}`);

export function FlipRoadmap({
  ledger,
  onRunNumbers,
}: {
  ledger: FlipLedger;
  onRunNumbers: (prefill: CalculatorPrefill) => void;
}) {
  const [levels, setLevels] = useState<RoadmapLevel[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getFlipRoadmap().then((d) => setLevels(d.levels)).catch((e) => setError(e.message));
  }, []);

  if (error) return <p className="text-sm text-red-400">{error}</p>;
  if (!levels) return <Skeleton className="h-64 w-full" />;

  const progress = ledger.summary?.progress;
  const current = progress?.current_level ?? 1;

  return (
    <div className="space-y-4">
      <Card className="p-5 text-sm text-muted">
        Start at Level 1 and move up as you prove you can buy, hold and sell without losing money.{" "}
        {progress?.rule ?? "Sell 2 flips at a level with an average result no worse than -$750 to graduate to the next."} Levels are advice,
        not locks - you can try any car, but higher levels cost more when you get it wrong.
      </Card>

      {levels.map((level) => {
        const stats = progress?.levels.find((l) => l.level === level.level);
        const isCurrent = level.level === current;
        const unlocked = stats ? stats.unlocked : level.level === 1;
        const graduated = stats?.graduated ?? false;
        return (
          <Card key={level.level} className={clsx("p-6", isCurrent && "ring-1 ring-[var(--accent)]", !unlocked && "opacity-70")}>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-wide text-muted">Level {level.level}</p>
                <h2 className="mt-0.5 text-xl font-semibold">{level.name}</h2>
                <p className="mt-1 text-sm text-muted">{level.tagline}</p>
              </div>
              <span
                className={clsx(
                  "rounded-full px-3 py-1 text-xs font-medium",
                  graduated ? "bg-green-400/15 text-green-300" : isCurrent ? "bg-[var(--accent)]/20 text-[var(--accent)]" : "bg-white/[0.06] text-muted"
                )}
              >
                {graduated ? "Completed" : isCurrent ? "You are here" : unlocked ? "Unlocked" : "Locked"}
              </span>
            </div>

            <p className="mt-4 text-sm">{level.why}</p>

            <div className="mt-4 grid gap-4 text-sm sm:grid-cols-2">
              <div>
                <p className="text-xs uppercase tracking-wide text-muted">Watch for</p>
                <ul className="mt-1 list-disc space-y-0.5 pl-5 text-muted">
                  {level.watch_for.map((w) => <li key={w}>{w}</li>)}
                </ul>
              </div>
              <div>
                <p className="text-xs uppercase tracking-wide text-muted">Buying rule</p>
                <p className="mt-1 text-muted">{level.buy_rule}</p>
                {stats && stats.flips_sold > 0 && (
                  <p className="mt-3 text-xs text-muted">
                    Your results here: {stats.flips_sold} sold, average {money(stats.avg_net)}
                  </p>
                )}
              </div>
            </div>

            <div className="mt-5">
              <p className="text-xs uppercase tracking-wide text-muted">Cars at this level</p>
              <div className="mt-2 flex flex-wrap gap-2">
                {level.cars.map((car) => (
                  <Button
                    key={`${car.make}-${car.model}`}
                    variant="secondary"
                    className="px-4 py-2 text-xs"
                    title={car.note}
                    onClick={() => onRunNumbers({ make: car.make, model: car.model })}
                  >
                    {car.make} {car.model}
                  </Button>
                ))}
              </div>
            </div>
          </Card>
        );
      })}
    </div>
  );
}
