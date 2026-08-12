// Small shared helper over the public Catalog shape (lib/types.ts), used
// anywhere the admin UI needs a flat, searchable list of generations rather
// than the nested make -> model -> generation tree the public cascading
// dropdowns use (ObservationCard's vehicle-match picker, the market
// aggregates viewer's generation picker).

import { Catalog, CatalogTrim } from "./types";

export interface FlatGeneration {
  id: number;
  label: string;
  trims: CatalogTrim[];
}

export function flattenGenerations(catalog: Catalog | null): FlatGeneration[] {
  if (!catalog) return [];
  return catalog.makes.flatMap((make) =>
    make.models.flatMap((model) =>
      model.generations.map((gen) => ({
        id: gen.id,
        label: `${make.name} ${model.name} — ${gen.label} (${gen.start_year}–${gen.end_year})`,
        trims: gen.trims,
      }))
    )
  );
}
