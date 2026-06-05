import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { SecuritySettings } from "@/pages/settings/SecuritySettings";

const mfaEnabled = vi.fn(() => false);

vi.mock("@/hooks/useAuth", () => ({
  useCurrentUser: () => ({ data: { full_name: "Maria", mfa_enabled: mfaEnabled() } }),
}));
vi.mock("@/hooks/useMFA", () => ({
  useDisableMFA: () => ({ mutate: vi.fn(), isPending: false }),
}));

function wrap() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <SecuritySettings />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("SecuritySettings", () => {
  it("oferece ativar quando o MFA está desligado", () => {
    mfaEnabled.mockReturnValue(false);
    wrap();
    expect(screen.getByRole("link", { name: /ativar/i })).toBeInTheDocument();
  });

  it("mostra estado ativado e botão desativar quando o MFA está ligado", () => {
    mfaEnabled.mockReturnValue(true);
    wrap();
    expect(screen.getByText(/ativada/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /desativar/i })).toBeInTheDocument();
  });
});
