import type { components } from "@/types/api.generated";

type FilterClause = components["schemas"]["FilterClause"];

export function toggleDimensionFilter(filters: FilterClause[], field: string, value: string): FilterClause[] {
  const selected = filters.find(item => item.field === field);
  const same = selected?.op === "in" && selected.values.length === 1 && String(selected.values[0]) === value;
  return [...filters.filter(item => item.field !== field), ...(same ? [] : [{ field, op: "in" as const, values: [value] }])];
}

export function comparisonSelection(dimension: string, valueA: string, valueB: string) {
  return dimension && valueA && valueB && valueA !== valueB
    ? { dimension, value_a: valueA, value_b: valueB }
    : undefined;
}
