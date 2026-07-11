import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { CadastroPage } from "@/pages/cadastros/CadastroPage";

vi.mock("@/lib/api", () => ({
  api: { get: vi.fn().mockResolvedValue({ data: { items: [], total: 0, limit: 50, offset: 0 } }) },
}));

function wrap(path: string) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/cadastros/:resource" element={<CadastroPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("CadastroPage", () => {
  it("renderiza o cadastro pelo slug da rota", () => {
    wrap("/cadastros/combustivel");
    expect(screen.getByRole("heading", { name: "Combustíveis" })).toBeInTheDocument();
  });

  it("mostra 'não encontrado' para slug inválido", () => {
    wrap("/cadastros/xyz");
    expect(screen.getByText(/não encontrado/i)).toBeInTheDocument();
  });
});
