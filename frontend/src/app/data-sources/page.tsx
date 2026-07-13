const SOURCE_ROWS = [
  {
    label: "Seller-provided listing information",
    detail:
      "Year, make, model, price, mileage, description text, and other fields you paste in or enter manually. VehicleGrade does not verify these against any external record.",
  },
  {
    label: "VehicleGrade reference database",
    detail:
      "Base market values, typical known issues, maintenance items, reliability ratings, and vehicle specifications, compiled and reviewed by us per vehicle generation. Coverage is currently focused on commonly-searched vehicles and is not exhaustive.",
  },
  {
    label: "User-provided comparable listings",
    detail:
      "Listings you add to the Comparison Workspace yourself. These come from wherever you found them and are not independently verified by VehicleGrade.",
  },
  {
    label: "Rule-based estimate",
    detail:
      "Numbers computed by an explicit formula from the sources above (e.g. the VehicleGrade Score, confidence score, and suggested offer). See the Methodology page for exactly how each is calculated.",
  },
  {
    label: "Official recall information",
    detail:
      "Where shown, sourced from official government or manufacturer recall databases rather than our own reference data.",
  },
];

export default function DataSourcesPage() {
  return (
    <div className="mx-auto max-w-3xl px-6 py-12">
      <h1 className="text-3xl font-semibold tracking-tight">Data Sources</h1>
      <p className="mt-2 text-muted">
        Every section of a VehicleGrade report is labeled with where its numbers come from. Here&apos;s
        what each label means.
      </p>

      <div className="mt-8 space-y-6">
        {SOURCE_ROWS.map((row) => (
          <div key={row.label} className="glass-card rounded-2xl p-5">
            <h2 className="text-base font-medium">{row.label}</h2>
            <p className="mt-1.5 text-sm text-muted">{row.detail}</p>
          </div>
        ))}
      </div>

      <p className="mt-8 text-sm text-muted">
        The Dashboard and Analytics pages currently run on a demo dataset of simulated listings,
        not live marketplace data. See the notice on those pages for details.
      </p>
    </div>
  );
}
