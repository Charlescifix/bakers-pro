import { useEffect, useState } from 'react';
import { Loader2, Plus, X } from 'lucide-react';
import { Button } from '../components/ui';
import { api } from '../lib/api';
import { extractApiError } from '../lib/api-errors';

type Customer = { id: string; full_name: string; company_name?: string };
type Variant = { id: string; name: string; product_name: string };
type ItemRow = { variant_id: string; quantity: string };

export default function QuoteBuilderModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: () => void;
}) {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [variants, setVariants] = useState<Variant[]>([]);
  const [loadingData, setLoadingData] = useState(true);
  const [fetchError, setFetchError] = useState('');

  const [customerId, setCustomerId] = useState('');
  const [deliveryMethod, setDeliveryMethod] = useState('pickup');
  const [notes, setNotes] = useState('');
  const [items, setItems] = useState<ItemRow[]>([{ variant_id: '', quantity: '1' }]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([
      api.get<Customer[]>('/customers'),
      api.get<{ id: string; name: string; variants: { id: string; name: string }[] }[]>('/products'),
    ])
      .then(([custRes, prodRes]) => {
        setCustomers(custRes.data ?? []);
        const flat: Variant[] = [];
        for (const prod of prodRes.data ?? []) {
          for (const v of prod.variants ?? []) {
            flat.push({ id: v.id, name: v.name, product_name: prod.name });
          }
        }
        setVariants(flat);
      })
      .catch(() => setFetchError('Failed to load customers and products. Please close and retry.'))
      .finally(() => setLoadingData(false));
  }, []);

  function addItem() {
    setItems((prev) => [...prev, { variant_id: '', quantity: '1' }]);
  }

  function removeItem(idx: number) {
    setItems((prev) => prev.filter((_, i) => i !== idx));
  }

  function updateItem(idx: number, field: keyof ItemRow, value: string) {
    setItems((prev) => prev.map((row, i) => (i === idx ? { ...row, [field]: value } : row)));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');

    const validItems = items.filter((r) => r.variant_id && parseInt(r.quantity) >= 1);
    if (!validItems.length) {
      setError('Add at least one item with a product variant selected and quantity ≥ 1.');
      return;
    }

    setSaving(true);
    try {
      const payload: Record<string, unknown> = {
        delivery_method: deliveryMethod,
        items: validItems.map((r) => ({
          product_variant_id: r.variant_id,
          quantity: parseInt(r.quantity),
        })),
      };
      if (customerId) payload.customer_id = customerId;
      if (notes.trim()) payload.internal_notes = notes.trim();

      await api.post('/quotes', payload);
      onCreated();
      onClose();
    } catch (err: unknown) {
      setError(extractApiError(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onClick={onClose}
    >
      <div
        className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-2xl bg-white p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-5 flex items-center justify-between">
          <h2 className="text-lg font-bold">New Quote</h2>
          <button onClick={onClose}>
            <X className="h-5 w-5 text-baker-muted" />
          </button>
        </div>

        {loadingData ? (
          <div className="flex items-center justify-center py-10">
            <Loader2 className="h-6 w-6 animate-spin text-brand" />
          </div>
        ) : fetchError ? (
          <div>
            <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{fetchError}</p>
            <Button variant="secondary" className="mt-4 w-full" onClick={onClose}>
              Close
            </Button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <label className="block text-sm font-semibold">
              Customer
              <select
                value={customerId}
                onChange={(e) => setCustomerId(e.target.value)}
                className="mt-1 w-full rounded-lg border border-baker-border px-3 py-2 text-sm outline-none focus:border-brand"
              >
                <option value="">No customer</option>
                {customers.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.full_name}
                    {c.company_name ? ` (${c.company_name})` : ''}
                  </option>
                ))}
              </select>
            </label>

            <label className="block text-sm font-semibold">
              Delivery Method
              <select
                value={deliveryMethod}
                onChange={(e) => setDeliveryMethod(e.target.value)}
                className="mt-1 w-full rounded-lg border border-baker-border px-3 py-2 text-sm outline-none focus:border-brand"
              >
                <option value="pickup">Pickup</option>
                <option value="local_delivery">Local Delivery</option>
                <option value="postal_delivery">Postal Delivery</option>
                <option value="courier">Courier</option>
                <option value="event_dropoff">Event Drop-off</option>
              </select>
            </label>

            <div>
              <div className="mb-2 flex items-center justify-between">
                <span className="text-sm font-semibold">Items *</span>
                <button
                  type="button"
                  onClick={addItem}
                  className="flex items-center gap-1 text-xs font-semibold text-brand hover:underline"
                >
                  <Plus className="h-3 w-3" /> Add Item
                </button>
              </div>

              {variants.length === 0 ? (
                <p className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-700">
                  No product variants found. Add a product with at least one variant first.
                </p>
              ) : (
                <div className="space-y-2">
                  {items.map((row, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      <select
                        value={row.variant_id}
                        onChange={(e) => updateItem(idx, 'variant_id', e.target.value)}
                        className="min-w-0 flex-1 rounded-lg border border-baker-border px-2 py-2 text-sm outline-none focus:border-brand"
                      >
                        <option value="">Select variant…</option>
                        {variants.map((v) => (
                          <option key={v.id} value={v.id}>
                            {v.product_name} – {v.name}
                          </option>
                        ))}
                      </select>
                      <input
                        type="number"
                        min="1"
                        step="1"
                        value={row.quantity}
                        onChange={(e) => updateItem(idx, 'quantity', e.target.value)}
                        placeholder="Qty"
                        className="w-16 rounded-lg border border-baker-border px-2 py-2 text-center text-sm outline-none focus:border-brand"
                      />
                      {items.length > 1 && (
                        <button
                          type="button"
                          onClick={() => removeItem(idx)}
                          className="shrink-0"
                        >
                          <X className="h-4 w-4 text-baker-muted hover:text-red-500" />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <label className="block text-sm font-semibold">
              Internal Notes
              <textarea
                rows={2}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="mt-1 w-full rounded-lg border border-baker-border px-3 py-2 text-sm outline-none focus:border-brand"
              />
            </label>

            {error && (
              <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
            )}

            <div className="flex gap-3 pt-2">
              <Button type="submit" disabled={saving} className="flex-1">
                {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Create Quote'}
              </Button>
              <Button type="button" variant="secondary" onClick={onClose}>
                Cancel
              </Button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
