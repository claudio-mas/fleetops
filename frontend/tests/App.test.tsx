import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import App from "../src/App";

describe("App", () => {
  it("renders the FleetOps headline", () => {
    render(<App />);
    expect(screen.getByRole("heading", { name: /FleetOps/i })).toBeInTheDocument();
  });

  it("shows the foundation skeleton message", () => {
    render(<App />);
    expect(screen.getByText(/Foundation skeleton ready/i)).toBeInTheDocument();
  });
});
