"use client";

import { useCallback, useEffect, useState } from "react";

import { ManualFormValue } from "@/components/analyze/ManualForm";
import { ListingDetail } from "@/lib/types";

// Versioned so a future incompatible shape change can migrate or safely
// discard old data instead of crashing on parse.
const STORAGE_KEY = "vehiclegrade:comparison-workspace:v1";
const MAX_ITEMS = 10;

export interface WorkspaceItem {
  id: string;
  formValue: ManualFormValue;
  report: ListingDetail | null;
}

function loadFromStorage(): WorkspaceItem[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    // Corrupt or unreadable storage - start fresh rather than crash the page.
    return [];
  }
}

function saveToStorage(items: WorkspaceItem[]) {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  } catch {
    // Quota exceeded or storage disabled - the workspace still works for the
    // current session, it just won't persist across reloads.
  }
}

// Account-free comparison workspace, persisted entirely in the browser.
// Nothing here is sent to the backend until the user explicitly analyzes a
// specific listing (see WorkspaceItemEditor).
export function useComparisonWorkspace() {
  const [items, setItems] = useState<WorkspaceItem[]>([]);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    setItems(loadFromStorage());
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (hydrated) saveToStorage(items);
  }, [items, hydrated]);

  const addItem = useCallback(() => {
    setItems((prev) => {
      if (prev.length >= MAX_ITEMS) return prev;
      return [...prev, { id: crypto.randomUUID(), formValue: {}, report: null }];
    });
  }, []);

  const removeItem = useCallback((id: string) => {
    setItems((prev) => prev.filter((item) => item.id !== id));
  }, []);

  const updateFormValue = useCallback((id: string, formValue: ManualFormValue) => {
    setItems((prev) => prev.map((item) => (item.id === id ? { ...item, formValue, report: null } : item)));
  }, []);

  const setReport = useCallback((id: string, report: ListingDetail | null) => {
    setItems((prev) => prev.map((item) => (item.id === id ? { ...item, report } : item)));
  }, []);

  return {
    items,
    hydrated,
    addItem,
    removeItem,
    updateFormValue,
    setReport,
    canAddMore: items.length < MAX_ITEMS,
  };
}
