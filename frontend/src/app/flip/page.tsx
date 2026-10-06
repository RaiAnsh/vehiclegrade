import { Suspense } from "react";

import { FlipHub } from "@/components/flip/FlipHub";

export const metadata = {
  title: "Flip Roadmap | VehicleGrade",
  description:
    "Buy, drive and resell cars in Ontario without losing money: a level-by-level roadmap, deal research, a profit calculator and a personal flip tracker.",
};

export default function FlipPage() {
  return (
    <div className="mx-auto max-w-4xl px-6 py-12">
      <h1 className="text-3xl font-semibold tracking-tight">Drive a better car every few months.</h1>
      <p className="mt-2 text-muted">
        Buy right, drive it, sell for about what you paid. Ontario private-sale costs &middot; HST &middot; insurance &middot; repairs
      </p>
      <div className="mt-8">
        <Suspense>
          <FlipHub />
        </Suspense>
      </div>
    </div>
  );
}
