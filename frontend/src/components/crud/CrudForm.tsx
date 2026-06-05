import { useEffect, useState } from "react";
import type { CadastroConfig } from "@/config/cadastros";
import { useCrudResource } from "@/hooks/useCrudResource";

interface Props {
  config: CadastroConfig;
  initial?: Record<string, unknown> | null;
  onClose: () => void;
}

function RefSelect({
  field,
  value,
  onChange,
}: {
  field: { refResource?: string; label: string };
  value: string;
  onChange: (v: string) => void;
}) {
  const ref = useCrudResource<{ id: string; nome: string; codigo?: string }>(field.refResource!);
  const { data } = ref.useList({ limit: 200 });
  return (
    <select
      className="w-full rounded border border-gray-300 px-3 py-2"
      value={value}
      onChange={(e) => onChange(e.target.value)}
    >
      <option value="">— selecione —</option>
      {data?.items.map((o) => (
        <option key={o.id} value={o.id}>
          {o.codigo ? `${o.codigo} — ${o.nome}` : o.nome}
        </option>
      ))}
    </select>
  );
}

export function CrudForm({ config, initial, onClose }: Props) {
  const create = useCrudResource(config.resource).useCreate();
  const update = useCrudResource(config.resource).useUpdate();
  const [values, setValues] = useState<Record<string, unknown>>({});
  const [error, setError] = useState<string | null>(null);
  const isEdit = initial != null;

  useEffect(() => {
    setValues(initial ?? {});
  }, [initial]);

  function set(name: string, v: unknown) {
    setValues((prev) => ({ ...prev, [name]: v }));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const payload: Record<string, unknown> = {};
    for (const f of config.fields) {
      const raw = values[f.name];
      payload[f.name] = raw === "" || raw === undefined ? null : raw;
    }
    try {
      if (isEdit) {
        payload.version = (initial as { version: number }).version;
        await update.mutateAsync({ id: (initial as { id: string }).id, data: payload });
      } else {
        await create.mutateAsync(payload);
      }
      onClose();
    } catch (err) {
      const detail = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Erro ao salvar");
    }
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <h3 className="text-lg font-semibold">
        {isEdit ? `Editar ${config.singular}` : `Novo ${config.singular}`}
      </h3>
      {config.fields.map((f) => (
        <div key={f.name} className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">
            {f.label}
            {f.required && <span className="text-red-500"> *</span>}
          </label>
          {f.type === "textarea" ? (
            <textarea
              className="w-full rounded border border-gray-300 px-3 py-2"
              value={String(values[f.name] ?? "")}
              onChange={(e) => set(f.name, e.target.value)}
            />
          ) : f.type === "ref" ? (
            <RefSelect
              field={f}
              value={String(values[f.name] ?? "")}
              onChange={(v) => set(f.name, v)}
            />
          ) : (
            <input
              type={f.type === "money" || f.type === "number" ? "number" : "text"}
              step={f.type === "money" ? "0.0001" : undefined}
              className="w-full rounded border border-gray-300 px-3 py-2"
              value={String(values[f.name] ?? "")}
              onChange={(e) => set(f.name, e.target.value)}
              required={f.required}
            />
          )}
        </div>
      ))}
      {error && <p className="text-sm text-red-600">{error}</p>}
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={create.isPending || update.isPending}
          className="rounded bg-blue-600 px-4 py-2 text-white disabled:opacity-50"
        >
          Salvar
        </button>
        <button type="button" onClick={onClose} className="rounded border px-4 py-2">
          Cancelar
        </button>
      </div>
    </form>
  );
}
