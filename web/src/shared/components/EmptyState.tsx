import type { LucideIcon } from "lucide-react";
import { cn } from "@/shared/lib/utils";

interface EmptyStateProps {
  readonly icon: LucideIcon;
  readonly title?: string;
  readonly description: string;
  readonly dashed?: boolean;
  readonly className?: string;
}

export function EmptyState({ icon: Icon, title, description, dashed = false, className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-3",
        dashed && "rounded-lg border border-dashed border-border py-14",
        className,
      )}
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-secondary">
        <Icon className="h-5 w-5 text-muted-foreground-dim" />
      </div>
      {title || description ? (
        <div className="text-center">
          {title && (
            <p className="text-sm font-medium text-foreground">{title}</p>
          )}
          <p className={cn("text-xs text-muted-foreground", title && "mt-0.5")}>
            {description}
          </p>
        </div>
      ) : null}
    </div>
  );
}
