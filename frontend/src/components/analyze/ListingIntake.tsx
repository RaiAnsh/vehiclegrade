"use client";

import { useCallback, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";

import { ListingPasteBox } from "@/components/analyze/ListingPasteBox";
import { ParsedListingConfirm } from "@/components/analyze/ParsedListingConfirm";
import { AnalyzingProgress } from "@/components/analyze/AnalyzingProgress";
import { ManualForm, ManualFormValue } from "@/components/analyze/ManualForm";
import { useListingIntake } from "@/hooks/useListingIntake";
import { ListingDetail } from "@/lib/types";

interface ListingIntakeProps {
  initialFormValue?: ManualFormValue;
  onFormValueChange?: (value: ManualFormValue) => void;
  onAnalyzed: (report: ListingDetail) => void;
  compact?: boolean;
}

// Orchestrates the paste -> parse -> confirm -> analyze flow shared by the
// homepage, /analyze, and each /compare workspace slot. Renders as an inline
// card that swaps content by stage (never a full-screen modal), since
// /compare needs several of these on screen at once, each independently
// mid-flow.
export function ListingIntake({ initialFormValue, onFormValueChange, onAnalyzed, compact }: ListingIntakeProps) {
  // The real report is held back from the parent until the analyzing
  // checklist finishes animating, so "Generating report..." never appears
  // to check itself off after the result is already visible below it.
  const [pendingReport, setPendingReport] = useState<ListingDetail | null>(null);

  const intake = useListingIntake({
    initialFormValue,
    onFormValueChange,
    onAnalyzed: setPendingReport,
  });

  const handleAnimationComplete = useCallback(() => {
    if (pendingReport) {
      onAnalyzed(pendingReport);
      setPendingReport(null);
    }
  }, [pendingReport, onAnalyzed]);

  // Stays true through the "done" stage until the checklist has actually
  // finished animating and handed the report off to the parent - otherwise
  // the progress card would unmount the instant the network call resolves,
  // before "Generating report..." ever gets to check itself off.
  const showAnalyzing = intake.stage === "analyzing" || (intake.stage === "done" && pendingReport !== null);

  return (
    <AnimatePresence mode="wait">
      {intake.stage === "paste" && (
        <motion.div key="paste" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: 0.35 }}>
          <ListingPasteBox
            onSubmit={intake.submitPaste}
            onEnterManually={intake.startEditing}
            loading={intake.parsing}
            error={intake.error}
            compact={compact}
          />
        </motion.div>
      )}

      {intake.stage === "confirming" && (
        <ParsedListingConfirm
          key="confirming"
          formValue={intake.formValue}
          aiFields={intake.aiFields}
          onEdit={intake.startEditing}
          onConfirm={intake.confirmAndAnalyze}
          error={intake.error}
          compact={compact}
        />
      )}

      {intake.stage === "editing" && (
        <motion.div key="editing" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: 0.35 }}>
          <ManualForm
            value={intake.formValue}
            onChange={intake.setFormValue}
            onSubmit={intake.confirmAndAnalyze}
            submitting={intake.analyzing}
            error={intake.error}
            aiFields={intake.aiFields}
          />
        </motion.div>
      )}

      {showAnalyzing && (
        <motion.div key="analyzing" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: 0.35 }}>
          <AnalyzingProgress done={pendingReport !== null} onComplete={handleAnimationComplete} compact={compact} />
        </motion.div>
      )}
    </AnimatePresence>
  );
}
