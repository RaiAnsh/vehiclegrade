"use client";

import { useCallback, useState } from "react";

import { ManualFormValue } from "@/components/analyze/ManualForm";
import { analyzeListing, parseListingText } from "@/lib/api";
import { AnalyzeInput, ListingDetail } from "@/lib/types";

export type IntakeStage = "paste" | "confirming" | "editing" | "analyzing" | "done";

interface UseListingIntakeOptions {
  initialFormValue?: ManualFormValue;
  onFormValueChange?: (value: ManualFormValue) => void;
  onAnalyzed: (report: ListingDetail) => void;
}

// Drives the paste -> parse -> confirm -> analyze flow shared by the
// homepage, /analyze, and each /compare workspace slot. Single-shot only -
// no memory, no streaming, no multi-turn conversation. Wraps the exact same
// parseListingText()/analyzeListing() calls the old dual-mode form used.
export function useListingIntake({ initialFormValue, onFormValueChange, onAnalyzed }: UseListingIntakeOptions) {
  // If this slot already has a draft (e.g. a /compare item restored from
  // localStorage), jump straight to the editable form instead of showing an
  // empty paste box in front of data the user already entered.
  const [stage, setStage] = useState<IntakeStage>(
    initialFormValue?.make && initialFormValue?.model ? "editing" : "paste"
  );
  const [formValue, setFormValueState] = useState<ManualFormValue>(initialFormValue ?? {});
  const [aiFields, setAiFields] = useState<string[]>([]);
  const [parsing, setParsing] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const setFormValue = useCallback(
    (value: ManualFormValue) => {
      setFormValueState(value);
      onFormValueChange?.(value);
    },
    [onFormValueChange]
  );

  const submitPaste = useCallback(
    (text: string) => {
      setParsing(true);
      setError(null);
      parseListingText(text)
        .then(({ _fields_from_ai, ...parsed }) => {
          // seller_rating/days_listed are required by POST /analyze but
          // aren't things a pasted listing ever states, so a neutral
          // default is applied here (never surfaced in the confirm card)
          // rather than forcing every paste back into the full manual form.
          setFormValue({
            seller_rating: 4,
            days_listed: 14,
            ...formValue,
            ...parsed,
          });
          setAiFields(_fields_from_ai ?? []);
          setStage("confirming");
        })
        .catch((err) => setError(err.message))
        .finally(() => setParsing(false));
    },
    [formValue, setFormValue]
  );

  const confirmAndAnalyze = useCallback(() => {
    setStage("analyzing");
    setAnalyzing(true);
    setError(null);
    analyzeListing(formValue as AnalyzeInput)
      .then((report) => {
        onAnalyzed(report);
        setStage("done");
      })
      .catch((err) => {
        setError(err.message);
        setStage("confirming");
      })
      .finally(() => setAnalyzing(false));
  }, [formValue, onAnalyzed]);

  const startEditing = useCallback(() => {
    setError(null);
    setStage("editing");
  }, []);

  const backToPaste = useCallback(() => {
    setError(null);
    setStage("paste");
  }, []);

  const reset = useCallback(() => {
    setFormValue({});
    setAiFields([]);
    setError(null);
    setStage("paste");
  }, [setFormValue]);

  return {
    stage,
    formValue,
    aiFields,
    parsing,
    analyzing,
    error,
    setFormValue,
    submitPaste,
    confirmAndAnalyze,
    startEditing,
    backToPaste,
    reset,
  };
}
