const compactFormatter = new Intl.NumberFormat('en-IN', {
  notation: 'compact',
  maximumFractionDigits: 1,
});

// Indian-style compact numbers (K, L, Cr) — used anywhere a count is shown
// in a tight space (bar lists, legends) so long numbers can't blow out the layout.
export function formatCompactNumber(value) {
  return typeof value === 'number' ? compactFormatter.format(value) : value ?? '—';
}
