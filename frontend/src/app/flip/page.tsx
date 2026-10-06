import { FlipCalculator } from "@/components/flip/FlipCalculator";

export const metadata = {
  title: "Flip Calculator | VehicleGrade",
  description: "Estimate the profit or loss of buying a used car privately in Ontario, holding it, and selling it.",
};

export default function FlipPage() {
  return (
    <div className="mx-auto max-w-4xl px-6 py-12">
      <h1 className="text-3xl font-semibold tracking-tight">Will this flip make money?</h1>
      <p className="mt-2 text-muted">
        Ontario private-sale costs &middot; HST &middot; insurance &middot; fuel &middot; repairs &middot; months held
      </p>
      <div className="mt-6">
        <FlipCalculator />
      </div>
    </div>
  );
}
