import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
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
        <Button onClick={() => setEditing(null)}>Novo</Button>
      </div>

      <Input
        placeholder="Buscar..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="max-w-sm"
      />

      {editing !== undefined && (
        <div className="rounded-lg border bg-muted/40 p-4">
          <CrudForm config={config} initial={editing} onClose={() => setEditing(undefined)} />
        </div>
      )}

      {isLoading ? (
        <p className="text-muted-foreground">Carregando...</p>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              {columns.map((c) => (
                <TableHead key={c.name}>{c.label}</TableHead>
              ))}
              <TableHead className="w-0" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {data?.items.map((row) => (
              <TableRow key={row.id}>
                {columns.map((c) => (
                  <TableCell key={c.name}>{String(row[c.name] ?? "—")}</TableCell>
                ))}
                <TableCell className="text-right whitespace-nowrap">
                  <Button variant="ghost" size="sm" onClick={() => setEditing(row)}>
                    Editar
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-destructive hover:text-destructive"
                    onClick={() => {
                      if (confirm("Excluir este registro?")) remove.mutate(row.id);
                    }}
                  >
                    Excluir
                  </Button>
                </TableCell>
              </TableRow>
            ))}
            {data && data.items.length === 0 && (
              <TableRow>
                <TableCell
                  colSpan={columns.length + 1}
                  className="py-6 text-center text-muted-foreground"
                >
                  Nenhum registro.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
