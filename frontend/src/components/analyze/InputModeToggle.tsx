import clsx from "clsx";

export type InputMode = "manual" | "paste";

interface InputModeToggleProps {
  mode: InputMode;
  onChange: (mode: InputMode) => void;
}

export function InputModeToggle({ mode, onChange }: InputModeToggleProps) {
  return (
    <div className="inline-flex rounded-full glass-card p-1">
      {(["manual", "paste"] as const).map((option) => (
        <button
          key={option}
          type="button"
          onClick={() => onChange(option)}
          className={clsx(
            "rounded-full px-5 py-2 text-sm font-medium transition-colors",
            mode === option ? "bg-[var(--accent)] text-white" : "text-muted hover:text-foreground"
          )}
        >
          {option === "manual" ? "Manual Entry" : "Paste Listing Text"}
        </button>
      ))}
    </div>
  );
}
