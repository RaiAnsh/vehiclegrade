import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "VehicleGrade — Vehicle Intelligence for Smarter Used Car Buyers",
  description:
    "Analyze used vehicle listings, estimate fair market value, uncover known issues, and negotiate smarter with a transparent, rule-based scoring engine.",
  verification: {
    google: "b9CQgRU51vNrsvB3F_tD9rolTWLXizwJmepacQT0lHk",
  },
};

// Anonymous usage analytics (Plausible), enabled only when
// NEXT_PUBLIC_PLAUSIBLE_DOMAIN is set. Plausible's script is a single
// lightweight tag with no cookies/no npm dependency, so it's added directly
// here rather than through an SDK. No-ops entirely if unset, since creating
// the actual Plausible/Umami account is something only the project owner
// can do.
const plausibleDomain = process.env.NEXT_PUBLIC_PLAUSIBLE_DOMAIN;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <head>
        {plausibleDomain && (
          <script defer data-domain={plausibleDomain} src="https://plausible.io/js/script.js" />
        )}
      </head>
      <body className="min-h-full flex flex-col">
        <Navbar />
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
