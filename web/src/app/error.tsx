"use client";

import { Button } from "@/shared/components/ui/button";

interface ErrorPageProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function ErrorPage({ error, reset }: ErrorPageProps) {
  return (
    <div className="flex h-screen w-screen items-center justify-center bg-background">
      <div className="flex flex-col items-center gap-4 text-center">
        <h1 className="text-xl font-semibold text-foreground">
          Something went wrong
        </h1>
        <p className="max-w-md text-sm text-muted-foreground">
          {error.message || "An unexpected error occurred."}
        </p>
        <Button onClick={reset}>
          Try again
        </Button>
      </div>
    </div>
  );
}
