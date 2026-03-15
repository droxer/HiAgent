import type { LucideIcon } from "lucide-react";
import { Button } from "@/shared/components/ui/button";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/shared/components/ui/tooltip";

interface IconButtonProps {
  icon: LucideIcon;
  label: string;
  size?: "icon-xs" | "icon-sm";
  onClick?: () => void;
  disabled?: boolean;
  type?: "button" | "submit";
  className?: string;
  variant?: "ghost" | "default";
}

export function IconButton({
  icon: Icon,
  label,
  size = "icon-sm",
  onClick,
  disabled,
  type = "button",
  className = "text-muted-foreground",
  variant = "ghost",
}: IconButtonProps) {
  const iconSize = size === "icon-xs" ? "h-3.5 w-3.5" : "h-4 w-4";

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          variant={variant}
          size={size}
          type={type}
          onClick={onClick}
          disabled={disabled}
          className={className}
        >
          <Icon className={iconSize} />
        </Button>
      </TooltipTrigger>
      <TooltipContent>{label}</TooltipContent>
    </Tooltip>
  );
}
