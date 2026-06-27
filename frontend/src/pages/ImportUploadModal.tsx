import { useRef, useState } from 'react';
import { Loader2, Upload, X } from 'lucide-react';
import { Button } from '../components/ui';
import { api } from '../lib/api';
import { extractApiError } from '../lib/api-errors';

export default function ImportUploadModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: () => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    const dropped = e.dataTransfer.files[0];
    if (dropped) setFile(dropped);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    setError('');
    setUploading(true);
    try {
      const form = new FormData();
      form.append('file', file);
      await api.post('/imports/upload', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      onCreated();
      onClose();
    } catch (err: unknown) {
      setError(extractApiError(err));
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
      <div
        className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-5 flex items-center justify-between">
          <h2 className="text-lg font-bold">Upload Cost Sheet</h2>
          <button onClick={onClose}><X className="h-5 w-5 text-baker-muted" /></button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
            className="flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed border-baker-border bg-cream/40 p-8 transition hover:border-brand hover:bg-cream"
          >
            <Upload className="h-8 w-8 text-baker-muted" />
            {file ? (
              <div className="text-center">
                <p className="font-semibold text-baker-text">{file.name}</p>
                <p className="text-xs text-baker-muted">{(file.size / 1024).toFixed(1)} KB</p>
              </div>
            ) : (
              <div className="text-center">
                <p className="font-semibold">Drop a file here, or click to browse</p>
                <p className="mt-1 text-xs text-baker-muted">Supports CSV, XLSX, PDF</p>
              </div>
            )}
            <input
              ref={inputRef}
              type="file"
              accept=".csv,.xlsx,.xls,.pdf"
              className="hidden"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
          </div>

          <p className="text-xs text-baker-muted">
            BakerProfit OS will auto-detect column mappings for ingredients, recipes, and pricing sheets. You can review the mapping before confirming.
          </p>

          {error && <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

          <div className="flex gap-3 pt-2">
            <Button type="submit" disabled={!file || uploading} className="flex-1">
              {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Upload & Analyse'}
            </Button>
            <Button type="button" variant="secondary" onClick={onClose}>Cancel</Button>
          </div>
        </form>
      </div>
    </div>
  );
}
