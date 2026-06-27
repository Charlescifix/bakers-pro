export function extractApiError(err: unknown): string {
  const data = (err as { response?: { data?: unknown } })?.response?.data;
  if (!data) return 'Save failed. Check required fields.';

  const detail = (data as { detail?: unknown }).detail;

  // Plain string from HTTPException
  if (typeof detail === 'string') return detail;

  // FastAPI Pydantic validation error (array of {loc, msg, type})
  if (Array.isArray(detail)) {
    return detail
      .map((e: { msg?: string; loc?: string[] }) => {
        const field = e.loc?.slice(1).join('.') ?? 'field';
        return `${field}: ${e.msg ?? 'invalid'}`;
      })
      .join('; ');
  }

  // BakerProfitError via HTTPException (detail is {error: {code, message, details}})
  if (detail && typeof detail === 'object') {
    const msg = (detail as { error?: { message?: string } }).error?.message;
    if (msg) return msg;
  }

  // BakerProfitError via global handler (top-level {error: {code, message, details}})
  const topMsg = (data as { error?: { message?: string } }).error?.message;
  if (topMsg) return topMsg;

  return 'Save failed. Check required fields.';
}
