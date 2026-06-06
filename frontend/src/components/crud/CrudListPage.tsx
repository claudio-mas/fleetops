import { useMemo, useState } from "react";
import {
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  Layers,
  MoreVertical,
  Pencil,
  Plus,
  Search,
  Trash2,
  Users,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { AvatarInitials } from "@/components/ui/avatar-initials";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { CadastroConfig, FieldConfig } from "@/config/cadastros";
import { useCrudResource } from "@/hooks/useCrudResource";
import { CrudForm } from "@/components/crud/CrudForm";

type Row = Record<string, unknown> & { id: string; version: number };

const PAGE_SIZE = 10;
const ALL = "__all__";

function StatusCell({ field, value }: { field: FieldConfig; value: string }) {
  const label = field.options?.find((o) => o.value === value)?.label ?? value;
  const variant =
    value === "ativo" ? "active" : value === "inativo" ? "inactive" : "neutral";
  return <Badge variant={variant}>{label}</Badge>;
}

function renderCell(field: FieldConfig, row: Row) {
  const raw = row[field.name];
  const value = raw == null || raw === "" ? null : String(raw);

  if (field.badge) {
    return value ? <StatusCell field={field} value={value} /> : <span className="text-muted-foreground">—</span>;
  }
  if (field.avatar) {
    if (!value) return <span className="text-muted-foreground">—</span>;
    return (
      <div className="flex items-center gap-2">
        <AvatarInitials name={value} />
        <span>{value}</span>
      </div>
    );
  }
  if (field.mono) {
    return value ? (
      <span className="font-medium tabular-nums text-foreground">{value}</span>
    ) : (
      <span className="text-muted-foreground">—</span>
    );
  }
  return value ?? <span className="text-muted-foreground">—</span>;
}

export function CrudListPage({ config }: { config: CadastroConfig }) {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>(ALL);
  const [page, setPage] = useState(0);
  const [editing, setEditing] = useState<Row | null | undefined>(undefined);

  const resource = useCrudResource<Row>(config.resource);
  const statusField = config.fields.find((f) => f.badge);
  const { data, isLoading } = resource.useList({
    search,
    limit: PAGE_SIZE,
    offset: page * PAGE_SIZE,
  });
  // Agregados reais (até 200 registros) para os cards-resumo.
  const { data: statsData } = resource.useList(
    statusField ? { search, limit: 200, offset: 0 } : { search, limit: 1, offset: 0 },
  );
  const remove = resource.useRemove();

  const columns = config.fields.filter((f) => f.listColumn);
  const total = data?.total ?? 0;
  const items = (data?.items ?? []).filter(
    (row) =>
      !statusField || statusFilter === ALL || String(row[statusField.name]) === statusFilter,
  );

  const stats = useMemo(() => {
    const rows = statsData?.items ?? [];
    const responsaveis = new Set(
      rows.map((r) => r["responsavel"]).filter((v) => v != null && v !== ""),
    );
    const inativos = rows.filter((r) => String(r["status"]) === "inativo").length;
    return { total: statsData?.total ?? 0, responsaveis: responsaveis.size, inativos };
  }, [statsData]);

  const from = total === 0 ? 0 : page * PAGE_SIZE + 1;
  const to = Math.min(total, (page + 1) * PAGE_SIZE);
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="space-y-6">
      {/* Cabeçalho + breadcrumb */}
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <nav className="mb-1 flex items-center gap-1 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
            <span>Configurações</span>
            <ChevronRight className="size-3.5" />
            <span className="text-primary">{config.label}</span>
          </nav>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">{config.label}</h1>
        </div>
        <Button onClick={() => setEditing(null)} className="gap-2 self-start md:self-auto">
          <Plus className="size-4" />
          Novo {config.singular.toLowerCase()}
        </Button>
      </div>

      {/* Formulário inline */}
      {editing !== undefined && (
        <div className="rounded-xl border bg-card p-6 shadow-sm">
          <CrudForm config={config} initial={editing} onClose={() => setEditing(undefined)} />
        </div>
      )}

      {/* Barra de filtros */}
      <div className="flex flex-col gap-4 rounded-xl border bg-card p-4 shadow-sm md:flex-row md:items-center md:justify-between">
        <div className="flex flex-col gap-3 md:flex-row md:items-center">
          <div className="relative w-full md:w-80">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Buscar por código ou descrição..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(0);
              }}
              className="pl-9"
            />
          </div>
          {statusField && (
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                Status
              </span>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[140px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Todos</SelectItem>
                  {statusField.options?.map((o) => (
                    <SelectItem key={o.value} value={o.value}>
                      {o.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
        </div>
        <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
          {total} {total === 1 ? config.singular.toLowerCase() : config.label.toLowerCase()}
        </span>
      </div>

      {/* Tabela */}
      <div className="overflow-hidden rounded-xl border border-t-4 border-t-primary bg-card shadow-sm">
        <Table>
          <TableHeader>
            <TableRow className="border-b bg-muted/60 hover:bg-muted/60">
              {columns.map((c) => (
                <TableHead
                  key={c.name}
                  className={`px-6 py-3 text-[11px] font-semibold uppercase tracking-wider text-foreground ${
                    c.align === "right" ? "text-right" : ""
                  }`}
                >
                  {c.listLabel ?? c.label}
                </TableHead>
              ))}
              <TableHead className="w-0 px-6 py-3 text-right text-[11px] font-semibold uppercase tracking-wider text-foreground">
                Ações
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={columns.length + 1} className="px-6 py-8 text-center text-muted-foreground">
                  Carregando...
                </TableCell>
              </TableRow>
            ) : items.length === 0 ? (
              <TableRow>
                <TableCell colSpan={columns.length + 1} className="px-6 py-8 text-center text-muted-foreground">
                  Nenhum registro.
                </TableCell>
              </TableRow>
            ) : (
              items.map((row) => (
                <TableRow key={row.id} className="hover:bg-primary/[0.04]">
                  {columns.map((c) => (
                    <TableCell
                      key={c.name}
                      className={`px-6 py-3 text-sm text-foreground ${
                        c.align === "right" ? "text-right" : ""
                      }`}
                    >
                      {renderCell(c, row)}
                    </TableCell>
                  ))}
                  <TableCell className="px-6 py-3 text-right">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="size-8 text-muted-foreground"
                          aria-label="Ações"
                        >
                          <MoreVertical className="size-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => setEditing(row)}>
                          <Pencil className="size-4" />
                          Editar
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          className="text-destructive focus:text-destructive"
                          onClick={() => {
                            if (confirm("Excluir este registro?")) remove.mutate(row.id);
                          }}
                        >
                          <Trash2 className="size-4" />
                          Excluir
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>

        {/* Paginação */}
        <div className="flex items-center justify-between border-t bg-card px-6 py-4">
          <span className="text-xs text-muted-foreground">
            Exibindo {from}-{to} de {total} registros
          </span>
          <div className="flex items-center gap-1">
            <Button
              variant="outline"
              size="icon"
              className="size-8"
              disabled={page === 0}
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              aria-label="Página anterior"
            >
              <ChevronLeft className="size-4" />
            </Button>
            <span className="px-2 text-sm font-semibold tabular-nums">
              {page + 1} / {pageCount}
            </span>
            <Button
              variant="outline"
              size="icon"
              className="size-8"
              disabled={page + 1 >= pageCount}
              onClick={() => setPage((p) => p + 1)}
              aria-label="Próxima página"
            >
              <ChevronRight className="size-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Cards-resumo (somente cadastros com status) */}
      {statusField && (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          <StatCard
            icon={<Layers className="size-20" />}
            label={`Total de ${config.label.toLowerCase()}`}
            value={String(stats.total)}
            hint="Registros cadastrados no tenant"
          />
          <StatCard
            icon={<Users className="size-20" />}
            label="Responsáveis distintos"
            value={String(stats.responsaveis)}
            hint="Gestores associados aos centros"
          />
          <StatCard
            icon={<AlertTriangle className="size-20" />}
            label="Centros inativos"
            value={String(stats.inativos)}
            hint={stats.inativos > 0 ? "Revise os centros desativados" : "Todos ativos"}
            tone={stats.inativos > 0 ? "error" : "default"}
          />
        </div>
      )}
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  hint,
  tone = "default",
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  hint: string;
  tone?: "default" | "error";
}) {
  return (
    <div className="group relative overflow-hidden rounded-xl border bg-card p-6 shadow-sm">
      <div className="absolute right-0 top-0 p-4 text-foreground opacity-[0.04] transition-opacity group-hover:opacity-[0.08]">
        {icon}
      </div>
      <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
        {label}
      </h3>
      <p
        className={`text-3xl font-bold tracking-tight ${
          tone === "error" ? "text-destructive" : "text-foreground"
        }`}
      >
        {value}
      </p>
      <p
        className={`mt-2 text-xs ${tone === "error" ? "text-destructive" : "text-muted-foreground"}`}
      >
        {hint}
      </p>
    </div>
  );
}
