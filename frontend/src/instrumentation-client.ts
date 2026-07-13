// Client-side error tracking, enabled only when NEXT_PUBLIC_SENTRY_DSN is
// set. Runs before the app becomes interactive (Next.js instrumentation-client
// convention). No-ops entirely if the DSN isn't configured, since creating
// the actual Sentry account/DSN is something only the project owner can do.

const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN;

if (dsn) {
  import("@sentry/browser").then(({ init }) => {
    init({
      dsn,
      environment: process.env.NEXT_PUBLIC_SENTRY_ENVIRONMENT ?? "production",
      tracesSampleRate: 0,
    });
  });
}
