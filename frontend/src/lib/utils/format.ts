export function formatDateTime(value?: string | null) {
  if (!value) return 'TBD';
  try {
    return new Intl.DateTimeFormat('en', {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(new Date(value));
  } catch {
    return value;
  }
}

export function formatPoints(value?: number | null) {
  return `${value ?? 0} pts`;
}
