import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { api } from "../src/lib/api";
import HealthCheck from "../src/pages/HealthCheck";

function wrap(children: ReactNode) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe("HealthCheck", () => {
  beforeEach(() => {
    vi.spyOn(api, "get").mockResolvedValue({
      data: { status: "ok" },
      status: 200,
      statusText: "OK",
      headers: {},
      config: {} as never,
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("displays the backend status when fetch succeeds", async () => {
    render(wrap(<HealthCheck />));
    await waitFor(() => {
      expect(screen.getByText(/backend status: ok/i)).toBeInTheDocument();
    });
  });

  it("calls /health endpoint", async () => {
    render(wrap(<HealthCheck />));
    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith("/health");
    });
  });
});
