import { SelectHTMLAttributes } from "react";
import clsx from "clsx";

export function Select({ className, children, ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={clsx(
        "w-full rounded-xl bg-white/[0.04] border border-white/10 px-4 py-2.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/50 transition-colors appearance-none cursor-pointer",
        className
      )}
      {...props}
    >
      {children}
    </select>
  );
}
