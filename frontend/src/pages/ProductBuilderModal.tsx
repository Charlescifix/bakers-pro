import { useEffect, useState } from 'react';
import { Loader2, Plus, X } from 'lucide-react';
import { Button } from '../components/ui';
import { api } from '../lib/api';
import { extractApiError } from '../lib/api-errors';

type Recipe = { id: string; name: string };
type VariantRow = { name: string; selling_price: string; margin: string; recipe_id: string };

export default function ProductBuilderModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: () => void;
}) {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [loadingData, setLoadingData] = useState(true);

  const [productName, setProductName] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('custom');
  const [variants, setVariants] = useState<VariantRow[]>([
    { name: '', selling_price: '', margin: '60', recipe_id: '' },
  ]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get<Recipe[]>('/recipes')
      .then((r) => setRecipes(r.data ?? []))
      .catch(() => {})
      .finally(() => setLoadingData(false));
  }, []);

  function addVariant() {
    setVariants((prev) => [...prev, { name: '', selling_price: '', margin: '60', recipe_id: '' }]);
  }

  function removeVariant(idx: number) {
    setVariants((prev) => prev.filter((_, i) => i !== idx));
  }

  function updateVariant(idx: number, field: keyof VariantRow, value: string) {
    setVariants((prev) => prev.map((row, i) => (i === idx ? { ...row, [field]: value } : row)));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');

    const validVariants = variants.filter((v) => v.name.trim());
    if (!validVariants.length) {
      setError('Add at least one variant with a name.');
      return;
    }

    setSaving(true);
    try {
      await api.post('/products', {
        name: productName.trim(),
        description: description.trim() || undefined,
        category,
        variants: validVariants.map((v) => ({
          name: v.name.trim(),
          current_selling_price: parseFloat(v.selling_price) || 0,
          desired_margin_percent: parseFloat(v.margin) || 60,
          recipe_id: v.recipe_id || undefined,
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
          <h2 className="text-lg font-bold">New Product</h2>
          <button onClick={onClose}><X className="h-5 w-5 text-baker-muted" /></button>
        </div>

        {loadingData ? (
          <div className="flex items-center justify-center py-10">
            <Loader2 className="h-6 w-6 animate-spin text-brand" />
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <label className="block text-sm font-semibold">
              Product Name *
              <input
                required
                value={productName}
                onChange={(e) => setProductName(e.target.value)}
                placeholder="e.g. Victoria Sponge"
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
                Description
                <input
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Optional"
                  className="mt-1 w-full rounded-lg border border-baker-border px-3 py-2 text-sm outline-none focus:border-brand"
                />
              </label>
            </div>

            <div>
              <div className="mb-2 flex items-center justify-between">
                <span className="text-sm font-semibold">Variants *</span>
                <button
                  type="button"
                  onClick={addVariant}
                  className="flex items-center gap-1 text-xs font-semibold text-brand hover:underline"
                >
                  <Plus className="h-3 w-3" /> Add Variant
                </button>
              </div>
              <p className="mb-2 text-xs text-baker-muted">e.g. "6-inch", "12-inch", "Box of 12"</p>

              <div className="space-y-3">
                {variants.map((row, idx) => (
                  <div key={idx} className="rounded-xl border border-baker-border bg-cream/40 p-3">
                    <div className="mb-2 flex items-center justify-between">
                      <span className="text-xs font-bold uppercase text-baker-muted">Variant {idx + 1}</span>
                      {variants.length > 1 && (
                        <button type="button" onClick={() => removeVariant(idx)}>
                          <X className="h-4 w-4 text-baker-muted hover:text-red-500" />
                        </button>
                      )}
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <label className="block text-xs font-semibold">
                        Variant Name *
                        <input
                          required
                          value={row.name}
                          onChange={(e) => updateVariant(idx, 'name', e.target.value)}
                          placeholder="e.g. 6-inch"
                          className="mt-1 w-full rounded-lg border border-baker-border px-2 py-1.5 text-sm outline-none focus:border-brand"
                        />
                      </label>
                      <label className="block text-xs font-semibold">
                        Selling Price (£)
                        <input
                          type="number"
                          min="0"
                          step="0.01"
                          value={row.selling_price}
                          onChange={(e) => updateVariant(idx, 'selling_price', e.target.value)}
                          placeholder="0.00"
                          className="mt-1 w-full rounded-lg border border-baker-border px-2 py-1.5 text-sm outline-none focus:border-brand"
                        />
                      </label>
                      <label className="block text-xs font-semibold">
                        Target Margin %
                        <input
                          type="number"
                          min="0"
                          max="100"
                          value={row.margin}
                          onChange={(e) => updateVariant(idx, 'margin', e.target.value)}
                          className="mt-1 w-full rounded-lg border border-baker-border px-2 py-1.5 text-sm outline-none focus:border-brand"
                        />
                      </label>
                      <label className="block text-xs font-semibold">
                        Recipe (optional)
                        <select
                          value={row.recipe_id}
                          onChange={(e) => updateVariant(idx, 'recipe_id', e.target.value)}
                          className="mt-1 w-full rounded-lg border border-baker-border px-2 py-1.5 text-sm outline-none focus:border-brand"
                        >
                          <option value="">No recipe</option>
                          {recipes.map((r) => (
                            <option key={r.id} value={r.id}>{r.name}</option>
                          ))}
                        </select>
                      </label>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {error && <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

            <div className="flex gap-3 pt-2">
              <Button type="submit" disabled={saving} className="flex-1">
                {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Create Product'}
              </Button>
              <Button type="button" variant="secondary" onClick={onClose}>Cancel</Button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
