import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { api } from "@/lib/api";
import { CrudListPage } from "@/components/crud/CrudListPage";
import { CADASTROS } from "@/config/cadastros";

vi.mock("@/lib/api", () => ({
  api: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
}));

function wrap(ui: React.ReactNode) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe("CrudListPage", () => {
  beforeEach(() => vi.clearAllMocks());

  it("renderiza o título e as linhas do recurso", async () => {
    (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: {
        items: [{ id: "1", nome: "Frota Pesada", responsavel: "João", version: 1 }],
        total: 1,
        limit: 50,
        offset: 0,
      },
    });
    render(wrap(<CrudListPage config={CADASTROS["centro-custo"]} />));
    expect(screen.getByRole("heading", { name: "Centros de Custo" })).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("Frota Pesada")).toBeInTheDocument());
  });
});
