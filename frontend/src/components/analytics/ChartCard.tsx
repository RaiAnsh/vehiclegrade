"use client";

import { ReactNode } from "react";
import { motion } from "framer-motion";

import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";

interface ChartCardProps {
  title: string;
  children: ReactNode;
  loading?: boolean;
  index?: number;
}

export function ChartCard({ title, children, loading, index = 0 }: ChartCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.06 }}
    >
      <Card className="p-6">
        <p className="mb-4 text-sm font-medium">{title}</p>
        {loading ? <Skeleton className="h-64 w-full" /> : <div className="h-64 w-full">{children}</div>}
      </Card>
    </motion.div>
  );
}
