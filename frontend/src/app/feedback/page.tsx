"use client";

import { FormEvent, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { submitFeedback } from "@/lib/api";

const CATEGORIES = [
  { value: "bug", label: "Something's broken" },
  { value: "inaccuracy", label: "A report looks inaccurate" },
  { value: "suggestion", label: "Suggestion" },
  { value: "other", label: "Other" },
];

export default function FeedbackPage() {
  const [message, setMessage] = useState("");
  const [email, setEmail] = useState("");
  const [category, setCategory] = useState("suggestion");
  const [status, setStatus] = useState<"idle" | "submitting" | "sent" | "error">("idle");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!message.trim()) return;

    setStatus("submitting");
    try {
      await submitFeedback({
        message: message.trim(),
        email: email.trim() || undefined,
        category,
        page_url: typeof window !== "undefined" ? window.location.href : undefined,
      });
      setStatus("sent");
      setMessage("");
      setEmail("");
    } catch {
      setStatus("error");
    }
  }

  return (
    <div className="mx-auto max-w-xl px-6 py-12">
      <h1 className="text-3xl font-semibold tracking-tight">Feedback</h1>
      <p className="mt-2 text-muted">
        Found something wrong, or have an idea for what VehicleGrade should do next? Tell us.
      </p>

      <Card className="mt-8 p-6">
        {status === "sent" ? (
          <p className="text-sm text-[var(--good)]">Thanks &mdash; your feedback was submitted.</p>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="mb-1.5 block text-sm text-muted">Category</label>
              <Select value={category} onChange={(e) => setCategory(e.target.value)}>
                {CATEGORIES.map((c) => (
                  <option key={c.value} value={c.value}>
                    {c.label}
                  </option>
                ))}
              </Select>
            </div>

            <div>
              <label className="mb-1.5 block text-sm text-muted">Message</label>
              <textarea
                required
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                rows={5}
                className="w-full rounded-xl border border-white/10 bg-white/[0.04] px-4 py-2.5 text-sm text-foreground placeholder:text-muted transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/50"
                placeholder="What did you notice?"
              />
            </div>

            <div>
              <label className="mb-1.5 block text-sm text-muted">Email (optional, for follow-up)</label>
              <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" />
            </div>

            {status === "error" && (
              <p className="text-sm text-[var(--avoid)]">
                Something went wrong submitting your feedback. Please try again.
              </p>
            )}

            <Button type="submit" disabled={status === "submitting"}>
              {status === "submitting" ? "Sending..." : "Send feedback"}
            </Button>
          </form>
        )}
      </Card>
    </div>
  );
}
