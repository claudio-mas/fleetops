import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CrudForm } from "@/components/crud/CrudForm";
import { CADASTROS } from "@/config/cadastros";

vi.mock("@/lib/api", () => ({
  api: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
}));

function wrap(ui: React.ReactNode) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>);
}

describe("CrudForm (shadcn)", () => {
  it("renderiza labels, inputs e botões para o cadastro", () => {
    wrap(<CrudForm config={CADASTROS["centro-custo"]} onClose={() => {}} />);
    expect(screen.getByText("Novo Centro de Custo")).toBeInTheDocument();
    expect(screen.getByLabelText(/Descrição/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Salvar" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Cancelar" })).toBeInTheDocument();
  });
});
