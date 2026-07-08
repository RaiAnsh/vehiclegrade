"use client";

import { motion } from "framer-motion";

import { Card } from "@/components/ui/Card";

const FEATURES = [
  {
    title: "Market Value Engine",
    description:
      "Estimates what a vehicle is objectively worth from its generation, trim, mileage, and title status - independent of the asking price.",
  },
  {
    title: "VehicleGrade Score",
    description:
      "A transparent 0-100 score comparing price to fair value, with every point traced back to a plain-English reason. No black boxes.",
  },
  {
    title: "Mileage-Aware Known Issues",
    description:
      "Every known issue for this generation, checked against the actual odometer reading - so you know what's relevant now versus years away.",
  },
  {
    title: "Negotiation Assistant",
    description:
      "A suggested opening offer, the reasoning behind it, and a ready-to-send message tuned to how the listing is priced and how long it's been sitting.",
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
