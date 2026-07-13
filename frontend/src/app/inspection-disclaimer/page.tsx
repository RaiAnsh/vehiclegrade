export default function InspectionDisclaimerPage() {
  return (
    <div className="mx-auto max-w-3xl px-6 py-12">
      <h1 className="text-3xl font-semibold tracking-tight">Inspection Disclaimer</h1>

      <div className="mt-8 space-y-4 text-sm leading-relaxed text-muted">
        <p>
          VehicleGrade is a preliminary research tool. It does not replace a professional
          pre-purchase inspection, vehicle-history report, lien search, or independent mechanical
          advice.
        </p>
        <p>
          Every score, market value, known issue, and repair estimate on this site is generated
          from listing information you provide and reference data we maintain. None of it is a
          substitute for physically inspecting the vehicle, having it examined by a qualified
          mechanic, or pulling an official vehicle-history and lien report before you buy.
        </p>
        <p>
          Known issues and maintenance estimates describe what is commonly seen on a given
          vehicle generation &mdash; they are not a guarantee that the specific vehicle you are
          looking at has, or does not have, any particular problem.
        </p>
        <p>
          Always verify title status, accident history, outstanding liens, and mechanical
          condition independently before completing a purchase.
        </p>
      </div>
    </div>
  );
}
