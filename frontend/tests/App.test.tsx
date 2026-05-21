import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import App from "../src/App";

function renderApp() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <App />
    </QueryClientProvider>,
  );
}

describe("App", () => {
  it("renders the FleetOps headline", () => {
    renderApp();
    expect(screen.getByRole("heading", { name: /FleetOps/i })).toBeInTheDocument();
  });

  it("shows the foundation skeleton message", () => {
    renderApp();
    expect(screen.getByText(/Foundation skeleton ready/i)).toBeInTheDocument();
  });
});
