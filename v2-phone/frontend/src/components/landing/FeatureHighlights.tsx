"use client";

import { motion } from "framer-motion";

import { Card } from "@/components/ui/Card";

const FEATURES = [
  {
    title: "Market Value Engine",
    description:
      "Estimates what a phone is objectively worth from its model, storage, condition, battery health, and lock status - independent of asking price.",
  },
  {
    title: "FlipIQ Score",
    description:
      "A transparent 0-100 score comparing price to fair value, with every point traced back to a plain-English reason. No black boxes.",
  },
  {
    title: "Suggested Offers",
    description:
      "A reasonable opening offer for every listing, tuned by how overpriced it is and how long it's been sitting on the market.",
  },
  {
    title: "Flip Profit Estimates",
    description:
      "See the estimated resale profit on any listing after marketplace fees, before you ever message the seller.",
  },
];

export function FeatureHighlights() {
  return (
    <section className="mx-auto max-w-6xl px-6 py-24">
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {FEATURES.map((feature, index) => (
          <motion.div
            key={feature.title}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 0.5, delay: index * 0.08 }}
          >
            <Card className="h-full p-6">
              <h3 className="text-base font-medium">{feature.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">{feature.description}</p>
            </Card>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
