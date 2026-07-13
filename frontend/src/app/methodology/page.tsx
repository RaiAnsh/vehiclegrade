export default function MethodologyPage() {
  return (
    <div className="mx-auto max-w-3xl px-6 py-12">
      <h1 className="text-3xl font-semibold tracking-tight">Methodology</h1>
      <p className="mt-2 text-muted">
        How VehicleGrade turns a listing into a score, a market value, and a set of known-issue
        and maintenance estimates. Every number below is produced by an explicit, rule-based
        calculation &mdash; there is no machine learning model deciding whether a car is a good
        deal.
      </p>

      <div className="mt-10 space-y-10 text-sm leading-relaxed text-muted">
        <section>
          <h2 className="text-lg font-medium text-foreground">Market value estimate</h2>
          <p className="mt-2">
            Each vehicle generation in our reference database has a base value and a reference
            mileage. A listing&apos;s estimated market value starts from that base value and is
            adjusted by percentage for: trim (relative to the base trim), mileage (higher mileage
            than the reference point lowers value, lower mileage raises it, capped at &minus;35%/+15%),
            title status (clean, unknown, rebuilt, or salvage), and condition (excellent, good,
            fair, or poor). The result is an independent estimate of what the vehicle is worth
            &mdash; it deliberately does not look at the seller&apos;s asking price, seller rating,
            or how long the listing has been posted.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-medium text-foreground">VehicleGrade Score (0&ndash;100)</h2>
          <p className="mt-2">
            The score starts at 50 and is adjusted by a fixed set of rules: how far the asking
            price sits below or above the estimated market value (the dominant factor), title
            status, how many known issues are already past their typical onset mileage, whether
            mileage is high or low for the vehicle&apos;s age, seller rating, and how long the
            listing has been posted. Every adjustment is shown to you as a plain-English reason
            with its point value, so the score can never say something the explanation doesn&apos;t
            back up.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-medium text-foreground">Known issues &amp; maintenance</h2>
          <p className="mt-2">
            Known issues are stored against a vehicle&apos;s generation in our reference database,
            each with a typical onset mileage. For a specific listing, we compare its actual
            mileage to that onset mileage to say whether an issue is not yet relevant, worth
            watching for, common at this mileage, or overdue. The underlying issue record never
            changes &mdash; only how it&apos;s presented changes based on the odometer reading in
            front of you.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-medium text-foreground">Confidence score</h2>
          <p className="mt-2">
            Confidence starts at 100 and is deducted for concrete, checkable gaps: few or no
            comparable listings for the vehicle&apos;s generation, an unidentified trim, a
            generation with no known-issue data recorded yet, missing mileage, or (for manually
            entered listings) optional fields left blank. Every deduction is shown with its
            reason, and anything that represents missing information is also listed explicitly
            so you know what to verify yourself.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-medium text-foreground">What VehicleGrade does not do</h2>
          <p className="mt-2">
            VehicleGrade does not use machine learning to judge reliability, market value, or
            deal quality. Where an AI language model is used, it is limited to turning numbers
            we&apos;ve already computed into a plain-language summary, or to extracting structured
            fields from a listing description &mdash; it never invents a known issue, a repair
            cost, or a score. See the <a href="/data-sources" className="underline underline-offset-2">Data Sources</a> page for
            where each report section&apos;s underlying numbers come from.
          </p>
        </section>
      </div>
    </div>
  );
}
