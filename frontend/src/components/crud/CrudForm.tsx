import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import type { CadastroConfig } from "@/config/cadastros";
import { useCrudResource } from "@/hooks/useCrudResource";

interface Props {
  config: CadastroConfig;
  initial?: Record<string, unknown> | null;
  onClose: () => void;
}

const NONE = "__none__";

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
    <Select
      value={value === "" ? undefined : value}
      onValueChange={(v) => onChange(v === NONE ? "" : v)}
    >
      <SelectTrigger>
        <SelectValue placeholder="— selecione —" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={NONE}>— Nenhum —</SelectItem>
        {data?.items.map((o) => (
          <SelectItem key={o.id} value={o.id}>
            {o.codigo ? `${o.codigo} — ${o.nome}` : o.nome}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

export function CrudForm({ config, initial, onClose }: Props) {
  const create = useCrudResource(config.resource).useCreate();
  const update = useCrudResource(config.resource).useUpdate();
  const [values, setValues] = useState<Record<string, unknown>>({});
  const [error, setError] = useState<string | null>(null);
  const isEdit = initial != null;

  useEffect(() => {
    if (initial) {
      setValues(initial);
    } else {
      const defaults: Record<string, unknown> = {};
      for (const f of config.fields) {
        if (f.defaultValue !== undefined) defaults[f.name] = f.defaultValue;
      }
      setValues(defaults);
    }
  }, [initial, config.fields]);

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
        <div key={f.name} className="space-y-1.5">
          <Label
            htmlFor={f.name}
            className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground"
          >
            {f.label}
            {f.required && <span className="text-destructive"> *</span>}
          </Label>
          {f.type === "textarea" ? (
            <Textarea
              id={f.name}
              value={String(values[f.name] ?? "")}
              onChange={(e) => set(f.name, e.target.value)}
            />
          ) : f.type === "ref" ? (
            <RefSelect
              field={f}
              value={String(values[f.name] ?? "")}
              onChange={(v) => set(f.name, v)}
            />
          ) : f.type === "select" ? (
            <Select
              value={String(values[f.name] ?? f.defaultValue ?? "")}
              onValueChange={(v) => set(f.name, v)}
            >
              <SelectTrigger id={f.name}>
                <SelectValue placeholder="— selecione —" />
              </SelectTrigger>
              <SelectContent>
                {f.options?.map((o) => (
                  <SelectItem key={o.value} value={o.value}>
                    {o.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ) : (
            <Input
              id={f.name}
              type={f.type === "money" || f.type === "number" ? "number" : "text"}
              step={f.type === "money" ? "0.0001" : undefined}
              value={String(values[f.name] ?? "")}
              onChange={(e) => set(f.name, e.target.value)}
              required={f.required}
            />
          )}
        </div>
      ))}
      {error && <p className="text-sm text-destructive">{error}</p>}
      <div className="flex gap-2">
        <Button type="submit" disabled={create.isPending || update.isPending}>
          Salvar
        </Button>
        <Button type="button" variant="outline" onClick={onClose}>
          Cancelar
        </Button>
      </div>
    </form>
  );
}
