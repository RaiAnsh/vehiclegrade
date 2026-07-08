"use client";

import { motion } from "framer-motion";

import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";

interface StatCardProps {
  label: string;
  value: string;
  index?: number;
}

export function StatCard({ label, value, index = 0 }: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.06 }}
    >
      <Card className="p-6">
        <p className="text-sm text-muted">{label}</p>
        <p className="mt-2 text-3xl font-semibold tracking-tight">{value}</p>
      </Card>
    </motion.div>
  );
}

export function StatCardSkeleton() {
  return (
    <Card className="p-6">
      <Skeleton className="h-4 w-24" />
      <Skeleton className="mt-3 h-8 w-16" />
    </Card>
  );
}
