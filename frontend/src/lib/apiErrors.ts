// Turns the browser's useless "Failed to fetch" into something a person (or
// whoever deployed this) can act on. fetch() only rejects for network-level
// failures, so anything caught here means the request never got a response.

export function describeNetworkError(apiUrl: string): string {
  const pointsAtLocalhost = /localhost|127\.0\.0\.1/.test(apiUrl);
  const onLocalhost = typeof window !== "undefined" && /^(localhost|127\.0\.0\.1)$/.test(window.location.hostname);

  if (pointsAtLocalhost && !onLocalhost) {
    return (
      `This site is trying to reach the API at ${apiUrl}, which only exists on a developer's own computer. ` +
      `The site owner needs to set NEXT_PUBLIC_API_URL to the deployed API address and redeploy the frontend.`
    );
  }
  if (pointsAtLocalhost) {
    return (
      `Couldn't reach the API at ${apiUrl}. Start the backend (cd backend && venv/bin/python run.py) and try again.`
    );
  }
  return (
    `Couldn't reach the VehicleGrade API at ${apiUrl}. The server may be down or restarting, ` +
    `or it may be rejecting this site's address (the API's ALLOWED_ORIGINS setting must include this site's URL).`
  );
}

export function describeHttpError(path: string, status: number, serverMessage?: string): string {
  if (serverMessage) return serverMessage;
  if (status === 404) return `The server doesn't have ${path} - it may be running an older version. Try again after the latest deploy finishes.`;
  if (status === 429) return "Too many requests - wait a minute and try again.";
  if (status >= 500) return `The server hit an error handling ${path} (${status}). Try again in a moment.`;
  return `Request to ${path} failed (${status}).`;
}
