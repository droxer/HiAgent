"use client";

import { Button } from "@/shared/components/ui/button";
import { useTranslation } from "@/i18n";

interface ErrorPageProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function ErrorPage({ error, reset }: ErrorPageProps) {
  const { t } = useTranslation();
  return (
    <div className="flex h-screen w-screen items-center justify-center bg-background">
      <div className="flex flex-col items-center gap-4 text-center">
        <h1 className="text-xl font-semibold text-foreground">
          {t("error.title")}
        </h1>
        <p className="max-w-md text-sm text-muted-foreground">
          {error.message || t("error.fallback")}
        </p>
        <Button onClick={reset}>
          {t("error.tryAgain")}
        </Button>
      </div>
    </div>
  );
}
