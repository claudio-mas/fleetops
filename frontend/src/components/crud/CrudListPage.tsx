import { useState } from "react";
import type { CadastroConfig } from "@/config/cadastros";
import { useCrudResource } from "@/hooks/useCrudResource";
import { CrudForm } from "@/components/crud/CrudForm";

type Row = Record<string, unknown> & { id: string; version: number };

export function CrudListPage({ config }: { config: CadastroConfig }) {
  const [search, setSearch] = useState("");
  const [editing, setEditing] = useState<Row | null | undefined>(undefined);
  const resource = useCrudResource<Row>(config.resource);
  const { data, isLoading } = resource.useList({ search });
  const remove = resource.useRemove();

  const columns = config.fields.filter((f) => f.listColumn);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">{config.label}</h2>
        <button
          onClick={() => setEditing(null)}
          className="rounded bg-blue-600 px-4 py-2 text-white"
        >
          Novo
        </button>
      </div>

      <input
        placeholder="Buscar..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="w-full max-w-sm rounded border border-gray-300 px-3 py-2"
      />

      {editing !== undefined && (
        <div className="rounded border border-gray-200 bg-gray-50 p-4">
          <CrudForm config={config} initial={editing} onClose={() => setEditing(undefined)} />
        </div>
      )}

      {isLoading ? (
        <p>Carregando...</p>
      ) : (
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b text-left">
              {columns.map((c) => (
                <th key={c.name} className="py-2 pr-4 font-medium">
                  {c.label}
                </th>
              ))}
              <th className="py-2" />
            </tr>
          </thead>
          <tbody>
            {data?.items.map((row) => (
              <tr key={row.id} className="border-b">
                {columns.map((c) => (
                  <td key={c.name} className="py-2 pr-4">
                    {String(row[c.name] ?? "—")}
                  </td>
                ))}
                <td className="py-2 text-right">
                  <button onClick={() => setEditing(row)} className="mr-3 text-blue-600">
                    Editar
                  </button>
                  <button
                    onClick={() => {
                      if (confirm("Excluir este registro?")) remove.mutate(row.id);
                    }}
                    className="text-red-600"
                  >
                    Excluir
                  </button>
                </td>
              </tr>
            ))}
            {data && data.items.length === 0 && (
              <tr>
                <td colSpan={columns.length + 1} className="py-6 text-center text-gray-500">
                  Nenhum registro.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}
