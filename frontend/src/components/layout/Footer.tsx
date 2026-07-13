import Image from "next/image";
import Link from "next/link";

import { StandardDisclaimer } from "./StandardDisclaimer";

const TRUST_LINKS = [
  { href: "/methodology", label: "Methodology" },
  { href: "/data-sources", label: "Data Sources" },
  { href: "/inspection-disclaimer", label: "Inspection Disclaimer" },
  { href: "/privacy", label: "Privacy" },
  { href: "/terms", label: "Terms" },
  { href: "/feedback", label: "Feedback" },
];

export function Footer() {
  return (
    <footer className="border-t border-white/5 py-10">
      <div className="mx-auto max-w-6xl px-6">
        <div className="flex flex-col items-center gap-4 text-center text-sm text-muted sm:flex-row sm:justify-between">
          <div className="flex items-center gap-3">
            <Image
              src="/circle_logo.png"
              alt="VehicleGrade.ca"
              width={1024}
              height={1024}
              className="h-8 w-8 rounded-full"
            />
            <p>VehicleGrade &mdash; Vehicle intelligence for smarter used car buyers.</p>
          </div>
          <nav className="flex flex-wrap items-center justify-center gap-4">
            {TRUST_LINKS.map((link) => (
              <Link key={link.href} href={link.href} className="transition-colors hover:text-foreground">
                {link.label}
              </Link>
            ))}
          </nav>
        </div>
        <div className="mt-6 border-t border-white/5 pt-6 text-center sm:text-left">
          <StandardDisclaimer />
        </div>
      </div>
    </footer>
  );
}
