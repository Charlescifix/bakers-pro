export function money(value: number, decimals = 2): string {
  return `£${Number(value || 0).toFixed(decimals)}`;
}

export function percent(value: number, decimals = 1): string {
  return `${Number(value || 0).toFixed(decimals)}%`;
}

export function marginTextClass(value: number): string {
  if (value < 0) return 'text-red-600';
  if (value < 40) return 'text-orange-600';
  if (value <= 60) return 'text-green-600';
  return 'text-green-700';
}

export function cx(...classes: Array<string | false | null | undefined>): string {
  return classes.filter(Boolean).join(' ');
}
