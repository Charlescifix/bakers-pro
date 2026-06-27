import { useEffect, useState } from 'react';
import { Loader2, Plus, X } from 'lucide-react';
import { Button } from '../components/ui';
import { api } from '../lib/api';
import { extractApiError } from '../lib/api-errors';

type Ingredient = { id: string; name: string; default_unit_code: string };
type ItemRow = { ingredient_id: string; quantity_used: string; unit_code: string };

export default function RecipeBuilderModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: () => void;
}) {
  const [ingredients, setIngredients] = useState<Ingredient[]>([]);
  const [loadingData, setLoadingData] = useState(true);
  const [fetchError, setFetchError] = useState('');

  const [name, setName] = useState('');
  const [category, setCategory] = useState('custom');
  const [yieldQty, setYieldQty] = useState('12');
  const [yieldUnit, setYieldUnit] = useState('item');
  const [labourMins, setLabourMins] = useState('60');
  const [notes, setNotes] = useState('');
  const [items, setItems] = useState<ItemRow[]>([{ ingredient_id: '', quantity_used: '', unit_code: '' }]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get<Ingredient[]>('/ingredients')
      .then((r) => setIngredients(r.data ?? []))
      .catch(() => setFetchError('Failed to load ingredients. Please close and retry.'))
      .finally(() => setLoadingData(false));
  }, []);

  function addItem() {
    setItems((prev) => [...prev, { ingredient_id: '', quantity_used: '', unit_code: '' }]);
  }

  function removeItem(idx: number) {
    setItems((prev) => prev.filter((_, i) => i !== idx));
  }

  function updateItem(idx: number, field: keyof ItemRow, value: string) {
    setItems((prev) =>
      prev.map((row, i) => {
        if (i !== idx) return row;
        const updated = { ...row, [field]: value };
        if (field === 'ingredient_id' && !row.unit_code) {
          const ing = ingredients.find((g) => g.id === value);
          if (ing?.default_unit_code) updated.unit_code = ing.default_unit_code;
        }
        return updated;
      }),
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');

    const validItems = items.filter((r) => r.ingredient_id && parseFloat(r.quantity_used) > 0 && r.unit_code);
    if (!validItems.length) {
      setError('Add at least one ingredient with quantity and unit filled in.');
      return;
    }

    setSaving(true);
    try {
      await api.post('/recipes', {
        name: name.trim(),
        category,
        base_yield_quantity: parseFloat(yieldQty),
        base_yield_unit: yieldUnit.trim() || 'item',
        labour_minutes_default: parseInt(labourMins) || 60,
        internal_notes: notes.trim() || undefined,
        items: validItems.map((r) => ({
          ingredient_id: r.ingredient_id,
          quantity_used: parseFloat(r.quantity_used),
          unit_code: r.unit_code.trim(),
        })),
      });
      onCreated();
      onClose();
    } catch (err: unknown) {
      setError(extractApiError(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
      <div
        className="max-h-[90vh] w-full max-w-xl overflow-y-auto rounded-2xl bg-white p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-5 flex items-center justify-between">
          <h2 className="text-lg font-bold">New Recipe</h2>
          <button onClick={onClose}><X className="h-5 w-5 text-baker-muted" /></button>
        </div>

        {loadingData ? (
          <div className="flex items-center justify-center py-10">
            <Loader2 className="h-6 w-6 animate-spin text-brand" />
          </div>
        ) : fetchError ? (
          <div>
            <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{fetchError}</p>
            <Button variant="secondary" className="mt-4 w-full" onClick={onClose}>Close</Button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <label className="block text-sm font-semibold">
              Recipe Name *
              <input
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Classic Victoria Sponge"
                className="mt-1 w-full rounded-lg border border-baker-border px-3 py-2 text-sm outline-none focus:border-brand"
              />
            </label>

            <div className="grid grid-cols-2 gap-3">
              <label className="block text-sm font-semibold">
                Category
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-baker-border px-3 py-2 text-sm outline-none focus:border-brand"
                >
                  {['custom', 'cake', 'bread', 'pastry', 'biscuit', 'celebration', 'savoury'].map((c) => (
                    <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
                  ))}
                </select>
              </label>

              <label className="block text-sm font-semibold">
                Labour (mins)
                <input
                  type="number"
                  min="1"
                  value={labourMins}
                  onChange={(e) => setLabourMins(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-baker-border px-3 py-2 text-sm outline-none focus:border-brand"
                />
              </label>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <label className="block text-sm font-semibold">
                Base Yield Qty *
                <input
                  type="number"
                  min="0.01"
                  step="any"
                  required
                  value={yieldQty}
                  onChange={(e) => setYieldQty(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-baker-border px-3 py-2 text-sm outline-none focus:border-brand"
                />
              </label>

              <label className="block text-sm font-semibold">
                Yield Unit
                <input
                  value={yieldUnit}
                  onChange={(e) => setYieldUnit(e.target.value)}
                  placeholder="item, g, slice…"
                  className="mt-1 w-full rounded-lg border border-baker-border px-3 py-2 text-sm outline-none focus:border-brand"
                />
              </label>
            </div>

            <div>
              <div className="mb-2 flex items-center justify-between">
                <span className="text-sm font-semibold">Ingredients *</span>
                <button
                  type="button"
                  onClick={addItem}
                  className="flex items-center gap-1 text-xs font-semibold text-brand hover:underline"
                >
                  <Plus className="h-3 w-3" /> Add Ingredient
                </button>
              </div>

              {ingredients.length === 0 ? (
                <p className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-700">
                  No ingredients found. Add ingredients first, then come back to build your recipe.
                </p>
              ) : (
                <div className="space-y-2">
                  {items.map((row, idx) => (
                    <div key={idx} className="grid grid-cols-[1fr_80px_80px_auto] items-center gap-2">
                      <select
                        value={row.ingredient_id}
                        onChange={(e) => updateItem(idx, 'ingredient_id', e.target.value)}
                        className="rounded-lg border border-baker-border px-2 py-2 text-sm outline-none focus:border-brand"
                      >
                        <option value="">Select…</option>
                        {ingredients.map((g) => (
                          <option key={g.id} value={g.id}>{g.name}</option>
                        ))}
                      </select>
                      <input
                        type="number"
                        min="0.01"
                        step="any"
                        value={row.quantity_used}
                        onChange={(e) => updateItem(idx, 'quantity_used', e.target.value)}
                        placeholder="Qty"
                        className="rounded-lg border border-baker-border px-2 py-2 text-center text-sm outline-none focus:border-brand"
                      />
                      <input
                        value={row.unit_code}
                        onChange={(e) => updateItem(idx, 'unit_code', e.target.value)}
                        placeholder="g / ml"
                        className="rounded-lg border border-baker-border px-2 py-2 text-center text-sm outline-none focus:border-brand"
                      />
                      {items.length > 1 && (
                        <button type="button" onClick={() => removeItem(idx)}>
                          <X className="h-4 w-4 text-baker-muted hover:text-red-500" />
                        </button>
                      )}
                    </div>
                  ))}
                  <p className="text-xs text-baker-muted">Ingredient → Quantity → Unit (g, ml, piece…)</p>
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

            {error && <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

            <div className="flex gap-3 pt-2">
              <Button type="submit" disabled={saving} className="flex-1">
                {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Create Recipe'}
              </Button>
              <Button type="button" variant="secondary" onClick={onClose}>Cancel</Button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
