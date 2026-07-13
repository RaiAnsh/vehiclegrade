export default function PrivacyPage() {
  return (
    <div className="mx-auto max-w-3xl px-6 py-12">
      <h1 className="text-3xl font-semibold tracking-tight">Privacy Policy</h1>
      <p className="mt-2 text-muted">Last updated July 2026.</p>

      <div className="mt-8 space-y-6 text-sm leading-relaxed text-muted">
        <section>
          <h2 className="text-base font-medium text-foreground">What we collect</h2>
          <p className="mt-2">
            Listing details you paste or enter for analysis, and comparison data you add to the
            Comparison Workspace, are processed to generate your report. Comparison Workspace data
            is stored in your browser&apos;s local storage and is not sent to our servers unless you
            explicitly submit a listing for analysis or opt in to contribute an anonymized
            comparable.
          </p>
          <p className="mt-2">
            If you submit feedback through the feedback form, we store the message, an optional
            email address (only if you provide one), an optional category, and the page you
            submitted it from.
          </p>
          <p className="mt-2">
            We may use anonymous, aggregate usage analytics (page views and feature usage) to
            understand how the product is used. This does not include the content of listings you
            analyze.
          </p>
        </section>

        <section>
          <h2 className="text-base font-medium text-foreground">What we don&apos;t collect</h2>
          <p className="mt-2">
            We do not require an account to use VehicleGrade. We do not collect seller names,
            seller profile URLs, phone numbers, street addresses, or private messages, including
            through the community comparable contribution feature.
          </p>
        </section>

        <section>
          <h2 className="text-base font-medium text-foreground">How we use it</h2>
          <p className="mt-2">
            Listing data is used solely to generate the report shown to you. Feedback is used to
            improve the product. Aggregate analytics are used to understand usage patterns, not to
            identify individual users.
          </p>
        </section>

        <section>
          <h2 className="text-base font-medium text-foreground">Contact</h2>
          <p className="mt-2">
            Questions about this policy can be sent through the <a href="/feedback" className="underline underline-offset-2">feedback form</a>.
          </p>
        </section>
      </div>
    </div>
  );
}
