import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { AppLayout } from "@/components/layout/AppLayout";

vi.mock("@/hooks/useAuth", () => ({
  useCurrentUser: () => ({ data: { full_name: "Maria Silva" } }),
  useLogout: () => ({ mutate: vi.fn() }),
}));

function wrap(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<div>CONTEUDO_INICIO</div>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
}

describe("AppLayout", () => {
  it("renderiza o conteúdo da rota filha no Outlet", () => {
    wrap("/dashboard");
    expect(screen.getByText("CONTEUDO_INICIO")).toBeInTheDocument();
  });

  it("mostra o título da rota na topbar", () => {
    wrap("/dashboard");
    expect(screen.getByRole("heading", { name: "Início" })).toBeInTheDocument();
  });
});
