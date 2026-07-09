import { ButtonHTMLAttributes } from "react";
import clsx from "clsx";

type Variant = "primary" | "secondary" | "ghost";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
}

const VARIANT_STYLES: Record<Variant, string> = {
  primary:
    "bg-[var(--accent)] text-white hover:bg-[#b8181f] shadow-[0_0_24px_-6px_var(--accent-soft)]",
  secondary: "glass-card text-foreground hover:bg-[var(--surface-hover)]",
  ghost: "text-muted hover:text-foreground",
};

export function Button({ variant = "primary", className, ...props }: ButtonProps) {
  return (
    <button
      className={clsx(
        "inline-flex items-center justify-center gap-2 rounded-full px-6 py-3 text-sm font-medium transition-all duration-200 active:scale-[0.97] disabled:opacity-50 disabled:pointer-events-none",
        VARIANT_STYLES[variant],
        className
      )}
      {...props}
    />
  );
}
