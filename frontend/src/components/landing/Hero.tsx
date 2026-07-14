"use client";

import Image from "next/image";
import Link from "next/link";
import { motion } from "framer-motion";

import { ListingIntake } from "@/components/analyze/ListingIntake";
import { ListingDetail } from "@/lib/types";

interface HeroProps {
  onAnalyzed: (report: ListingDetail) => void;
}

export function Hero({ onAnalyzed }: HeroProps) {
  return (
    <section className="relative flex min-h-[70vh] items-center justify-center px-6 py-16">
      <div className="relative mx-auto w-full max-w-2xl text-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.4, rotate: -25 }}
          animate={{ opacity: 1, scale: 1, rotate: 0, y: [0, -8, 0] }}
          transition={{
            opacity: { duration: 0.7, ease: [0.16, 1, 0.3, 1] },
            scale: { duration: 0.7, ease: [0.16, 1, 0.3, 1] },
            rotate: { duration: 0.7, ease: [0.16, 1, 0.3, 1] },
            y: { duration: 4, repeat: Infinity, ease: "easeInOut", delay: 0.7 },
          }}
          className="mx-auto mb-5 h-14 w-14"
        >
          <Image
            src="/circle_logo.png"
            alt="VehicleGrade.ca"
            width={256}
            height={256}
            priority
            className="h-full w-full drop-shadow-[0_0_35px_rgba(220,38,38,0.4)]"
          />
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.15 }}
          className="text-3xl font-semibold tracking-tight sm:text-5xl"
        >
          Research a used vehicle <span className="accent-gradient-text">in seconds.</span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.25 }}
          className="mx-auto mt-4 max-w-lg text-muted"
        >
          Paste any listing &mdash; Marketplace, AutoTrader, Kijiji, or a dealer site &mdash; and get a full vehicle
          intelligence report back.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.35 }}
          className="mt-8 text-left"
        >
          <ListingIntake onAnalyzed={onAnalyzed} />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.45 }}
          className="mt-6 flex flex-wrap items-center justify-center gap-4 text-sm"
        >
          <Link href="/dashboard" className="text-muted hover:text-foreground">
            Try Demo
          </Link>
          <span className="text-muted">&middot;</span>
          <a
            href="https://github.com/RaiAnsh/vehiclegrade"
            target="_blank"
            rel="noreferrer"
            className="text-muted hover:text-foreground"
          >
            View GitHub
          </a>
        </motion.div>
      </div>
    </section>
  );
}
