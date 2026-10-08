"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { summarizeFlipLedger } from "@/lib/api";
import { ExpenseCategory, FlipLedgerSummary, LocalFlip } from "@/lib/types";

const STORAGE_KEY = "vehiclegrade.flips.v1";

function load(): LocalFlip[] {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return []; // storage blocked or corrupt - start empty rather than crash
  }
}

function newId() {
  return typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

const today = () => new Date().toISOString().slice(0, 10);

// Flips are stored only in this browser. The server computes the numbers
// (profit/loss, actual vs predicted, level progress) from what we send but
// never stores it, so there's no account and nothing to leak.
export function useFlipLedger() {
  const [flips, setFlips] = useState<LocalFlip[]>([]);
  const [ready, setReady] = useState(false);
  const [summary, setSummary] = useState<FlipLedgerSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [storageWorks, setStorageWorks] = useState(true);
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    setFlips(load());
    setReady(true);
  }, []);

  useEffect(() => {
    if (!ready) return;
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(flips));
    } catch {
      setStorageWorks(false);
    }
  }, [flips, ready]);

  useEffect(() => {
    if (!ready) return;
    let cancelled = false;
    // Always ask the server, even with no flips, so the roadmap still gets a
    // well-formed (level 1) progress object.
    summarizeFlipLedger(flips)
      .then((data) => {
        if (!cancelled) {
          setSummary(data);
          setError(null);
        }
      })
      .catch((e) => !cancelled && setError(e instanceof Error ? e.message : "Could not compute your ledger"));
    return () => {
      cancelled = true;
    };
  }, [flips, ready, retryCount]);

  const retry = useCallback(() => setRetryCount((n) => n + 1), []);

  const addFlip = useCallback((flip: Omit<LocalFlip, "id" | "status" | "expenses" | "purchase_date"> & { purchase_date?: string }) => {
    const created: LocalFlip = { ...flip, id: newId(), status: "holding", expenses: [], purchase_date: flip.purchase_date ?? today() };
    setFlips((prev) => [created, ...prev]);
    return created.id;
  }, []);

  const addExpense = useCallback((id: string, category: ExpenseCategory, amount: number, note?: string) => {
    setFlips((prev) =>
      prev.map((f) => (f.id === id ? { ...f, expenses: [...f.expenses, { id: newId(), date: today(), category, amount, note }] } : f))
    );
  }, []);

  const removeExpense = useCallback((id: string, expenseId: string) => {
    setFlips((prev) => prev.map((f) => (f.id === id ? { ...f, expenses: f.expenses.filter((e) => e.id !== expenseId) } : f)));
  }, []);

  const sell = useCallback((id: string, sale_price: number, sale_fees: number, sale_date?: string) => {
    setFlips((prev) => prev.map((f) => (f.id === id ? { ...f, status: "sold", sale_price, sale_fees, sale_date: sale_date || today() } : f)));
  }, []);

  const remove = useCallback((id: string) => setFlips((prev) => prev.filter((f) => f.id !== id)), []);

  const replaceAll = useCallback((next: LocalFlip[]) => setFlips(next), []);

  return useMemo(
    () => ({ flips, ready, summary, error, retry, storageWorks, addFlip, addExpense, removeExpense, sell, remove, replaceAll }),
    [flips, ready, summary, error, retry, storageWorks, addFlip, addExpense, removeExpense, sell, remove, replaceAll]
  );
}

export type FlipLedger = ReturnType<typeof useFlipLedger>;
