import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { AppSidebar } from "@/components/layout/AppSidebar";
import { SidebarProvider } from "@/components/ui/sidebar";
import { CADASTROS } from "@/config/cadastros";

const logout = vi.fn();

vi.mock("@/hooks/useAuth", () => ({
  useCurrentUser: () => ({ data: { full_name: "Maria Silva" } }),
  useLogout: () => ({ mutate: logout }),
}));

function wrap(path = "/cadastros/centro-custo") {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <SidebarProvider>
        <AppSidebar />
      </SidebarProvider>
    </MemoryRouter>,
  );
}

describe("AppSidebar", () => {
  it("mostra Início e os 11 cadastros a partir da config", () => {
    wrap();
    expect(screen.getByText("Início")).toBeInTheDocument();
    for (const c of Object.values(CADASTROS)) {
      expect(screen.getByText(c.label)).toBeInTheDocument();
    }
  });

  it("os itens de cadastro apontam para /cadastros/<slug>", () => {
    wrap();
    const link = screen.getByRole("link", { name: CADASTROS["combustivel"].label });
    expect(link).toHaveAttribute("href", "/cadastros/combustivel");
  });

  it("o botão Sair dispara logout", async () => {
    wrap();
    await userEvent.click(screen.getByText("Sair"));
    expect(logout).toHaveBeenCalled();
  });

  it("exibe o nome do usuário", () => {
    wrap();
    expect(screen.getByText("Maria Silva")).toBeInTheDocument();
  });
});
