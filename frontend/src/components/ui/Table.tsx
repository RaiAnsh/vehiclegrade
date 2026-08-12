import { HTMLAttributes, TdHTMLAttributes, ThHTMLAttributes } from "react";
import clsx from "clsx";

// Minimal table primitives for admin data grids (review queues, batch
// lists). Not used by the public app, which has no tabular data views.

export function Table({ className, ...props }: HTMLAttributes<HTMLTableElement>) {
  return (
    <div className="w-full overflow-x-auto rounded-2xl border border-white/10">
      <table className={clsx("w-full border-collapse text-left text-sm", className)} {...props} />
    </div>
  );
}

export function Thead({ className, ...props }: HTMLAttributes<HTMLTableSectionElement>) {
  return <thead className={clsx("bg-white/[0.03] text-xs uppercase tracking-wide text-muted", className)} {...props} />;
}

export function Tbody({ className, ...props }: HTMLAttributes<HTMLTableSectionElement>) {
  return <tbody className={clsx("divide-y divide-white/5", className)} {...props} />;
}

export function Tr({ className, ...props }: HTMLAttributes<HTMLTableRowElement>) {
  return <tr className={clsx("transition-colors hover:bg-white/[0.02]", className)} {...props} />;
}

export function Th({ className, ...props }: ThHTMLAttributes<HTMLTableCellElement>) {
  return <th className={clsx("px-4 py-3 font-medium", className)} {...props} />;
}

export function Td({ className, ...props }: TdHTMLAttributes<HTMLTableCellElement>) {
  return <td className={clsx("px-4 py-3 align-middle", className)} {...props} />;
}
