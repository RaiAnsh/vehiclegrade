"use client";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

export function ErrorCard({ title, message, onRetry }: { title: string; message: string; onRetry?: () => void }) {
  return (
    <Card className="border border-red-400/30 p-6" role="alert">
      <p className="text-sm font-medium text-red-300">{title}</p>
      <p className="mt-2 text-sm text-muted">{message}</p>
      {onRetry && (
        <Button variant="secondary" className="mt-4" onClick={onRetry}>
          Try again
        </Button>
      )}
    </Card>
  );
}
