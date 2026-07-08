import Link from "next/link";

const LINKS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/analytics", label: "Analytics" },
  { href: "/analyze", label: "Analyze" },
];

export function Navbar() {
  return (
    <header className="sticky top-0 z-40 border-b border-white/5 bg-[var(--background)]/70 backdrop-blur-xl">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="flex items-center gap-2 text-lg font-semibold">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-[var(--accent)] text-sm text-white">
            F
          </span>
          FlipIQ
        </Link>

        <nav className="hidden items-center gap-8 text-sm text-muted sm:flex">
          {LINKS.map((link) => (
            <Link key={link.href} href={link.href} className="transition-colors hover:text-foreground">
              {link.label}
            </Link>
          ))}
        </nav>

        {/* TODO: replace with your actual FlipIQ repo URL */}
        <a
          href="https://github.com"
          target="_blank"
          rel="noreferrer"
          className="rounded-full glass-card px-4 py-2 text-sm transition-colors hover:bg-[var(--surface-hover)]"
        >
          GitHub
        </a>
      </div>
    </header>
  );
}
