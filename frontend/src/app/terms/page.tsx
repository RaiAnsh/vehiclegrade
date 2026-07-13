export default function TermsPage() {
  return (
    <div className="mx-auto max-w-3xl px-6 py-12">
      <h1 className="text-3xl font-semibold tracking-tight">Terms of Use</h1>
      <p className="mt-2 text-muted">Last updated July 2026.</p>

      <div className="mt-8 space-y-6 text-sm leading-relaxed text-muted">
        <section>
          <h2 className="text-base font-medium text-foreground">Research tool, not professional advice</h2>
          <p className="mt-2">
            VehicleGrade is a preliminary research tool provided for informational purposes only.
            It does not replace a professional pre-purchase inspection, vehicle-history report,
            lien search, or independent mechanical advice. See the{" "}
            <a href="/inspection-disclaimer" className="underline underline-offset-2">Inspection Disclaimer</a>{" "}
            for details.
          </p>
        </section>

        <section>
          <h2 className="text-base font-medium text-foreground">No warranty</h2>
          <p className="mt-2">
            VehicleGrade is provided &quot;as is&quot; without warranty of any kind. We make no
            guarantee that any score, market value estimate, known issue, or repair cost estimate
            is accurate or complete for any specific vehicle. Use of this site is at your own
            risk, and you are responsible for independently verifying any information before
            making a purchase decision.
          </p>
        </section>

        <section>
          <h2 className="text-base font-medium text-foreground">Acceptable use</h2>
          <p className="mt-2">
            Do not use VehicleGrade to submit listing data, feedback, or community comparable
            contributions that contain another person&apos;s private information, or to attempt to
            disrupt or misuse the service.
          </p>
        </section>

        <section>
          <h2 className="text-base font-medium text-foreground">Changes</h2>
          <p className="mt-2">
            These terms may be updated as the product evolves. Continued use of VehicleGrade after
            a change constitutes acceptance of the updated terms.
          </p>
        </section>
      </div>
    </div>
  );
}
