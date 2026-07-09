"use client";

import Link from "next/link";
import { motion } from "framer-motion";

import { Button } from "@/components/ui/Button";
import { GradientBackground } from "./GradientBackground";

export function Hero() {
  return (
    <section className="relative flex min-h-[85vh] items-center justify-center px-6">
      <GradientBackground />

      <div className="relative mx-auto max-w-3xl text-center">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-6 inline-flex items-center gap-2 rounded-full glass-card px-4 py-1.5 text-xs text-muted"
        >
          Rule-based vehicle intelligence &middot; No machine learning
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.05 }}
          className="text-4xl font-semibold tracking-tight sm:text-6xl"
        >
          Should You Buy That{" "}
          <span className="accent-gradient-text">Used Car?</span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.15 }}
          className="mx-auto mt-6 max-w-xl text-lg text-muted"
        >
          Analyze listings, estimate fair market value, uncover known issues
          before they surface, and negotiate smarter &mdash; all before you
          ever call the seller.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.25 }}
          className="mt-10 flex flex-wrap items-center justify-center gap-4"
        >
          <Link href="/dashboard">
            <Button variant="primary">Try Demo</Button>
          </Link>
          <a href="https://github.com/RaiAnsh/vehiclegrade" target="_blank" rel="noreferrer">
            <Button variant="secondary">View GitHub</Button>
          </a>
        </motion.div>
      </div>
    </section>
  );
}
