import Image from "next/image";
import Link from "next/link";

const LINKS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/analytics", label: "Analytics" },
  { href: "/analyze", label: "Analyze" },
  { href: "/compare", label: "Compare" },
];

export function Navbar() {
  return (
    <header className="sticky top-0 z-40 border-b border-white/5 bg-[var(--background)]/70 backdrop-blur-xl">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="flex items-center">
          <Image
            src="/logo.png"
            alt="VehicleGrade.ca"
            width={1536}
            height={1024}
            priority
            className="h-10 w-auto"
          />
        </Link>

        <nav className="hidden items-center gap-8 text-sm text-muted sm:flex">
          {LINKS.map((link) => (
            <Link key={link.href} href={link.href} className="transition-colors hover:text-foreground">
              {link.label}
            </Link>
          ))}
        </nav>

        <a
          href="https://github.com/RaiAnsh/vehiclegrade"
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
