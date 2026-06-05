import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { api } from "@/lib/api";
import { useCrudResource } from "@/hooks/useCrudResource";

vi.mock("@/lib/api", () => ({
  api: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
}));

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe("useCrudResource", () => {
  beforeEach(() => vi.clearAllMocks());

  it("lista itens do recurso paginado", async () => {
    (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: { items: [{ id: "1", nome: "A" }], total: 1, limit: 50, offset: 0 },
    });
    const resource = useCrudResource<{ id: string; nome: string }>("centro-custo");
    const { result } = renderHook(() => resource.useList({ search: "" }), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(api.get).toHaveBeenCalledWith(
      "/v1/cadastros/centro-custo",
      expect.objectContaining({ params: expect.any(Object) }),
    );
    expect(result.current.data?.total).toBe(1);
  });
});
