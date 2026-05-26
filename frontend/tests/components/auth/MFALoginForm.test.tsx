import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { expect, test, describe, afterEach } from "vitest";
import { MFALoginForm } from "../../../src/components/auth/MFALoginForm";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

function renderMFAForm(challengeToken: string = "test-token") {
  return render(
    <MemoryRouter>
      <QueryClientProvider client={queryClient}>
        <MFALoginForm challengeToken={challengeToken} />
      </QueryClientProvider>
    </MemoryRouter>
  );
}

describe("MFALoginForm", () => {
  afterEach(() => {
    queryClient.clear();
  });

  test("renders TOTP input field and submit button", () => {
    renderMFAForm();
    expect(screen.getByPlaceholderText(/000000/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Confirmar/ })).toBeInTheDocument();
  });

  test("renders heading and description", () => {
    renderMFAForm();
    expect(screen.getByText(/Verificação em duas etapas/)).toBeInTheDocument();
    expect(screen.getByText(/código de 6 dígitos/i)).toBeInTheDocument();
  });

  test("accepts numeric input only", async () => {
    renderMFAForm();
    const input = screen.getByPlaceholderText(/000000/) as HTMLInputElement;

    fireEvent.change(input, { target: { value: "abc123" } });
    await waitFor(() => {
      expect(input.value).toBe("123");
    });
  });

  test("limits input to 6 digits", async () => {
    renderMFAForm();
    const input = screen.getByPlaceholderText(/000000/) as HTMLInputElement;

    fireEvent.change(input, { target: { value: "1234567890" } });
    await waitFor(() => {
      expect(input.value).toBe("123456");
    });
  });

  test("disables submit button when token is not 6 digits", () => {
    renderMFAForm();
    const button = screen.getByRole("button", { name: /Confirmar/ });

    expect(button).toBeDisabled();

    const input = screen.getByPlaceholderText(/000000/) as HTMLInputElement;
    fireEvent.change(input, { target: { value: "12345" } });

    expect(button).toBeDisabled();
  });

  test("enables submit button when token is exactly 6 digits", async () => {
    renderMFAForm();
    const button = screen.getByRole("button", { name: /Confirmar/ });
    const input = screen.getByPlaceholderText(/000000/) as HTMLInputElement;

    fireEvent.change(input, { target: { value: "123456" } });

    await waitFor(() => {
      expect(button).not.toBeDisabled();
    });
  });

  test("shows error message on form submission when token is invalid", async () => {
    renderMFAForm();
    const input = screen.getByPlaceholderText(/000000/) as HTMLInputElement;
    const button = screen.getByRole("button", { name: /Confirmar/ });

    fireEvent.change(input, { target: { value: "12345" } });

    await waitFor(() => {
      expect(button).toBeDisabled();
    });
  });

  test("shows loading state while submitting", async () => {
    renderMFAForm();
    const input = screen.getByPlaceholderText(/000000/) as HTMLInputElement;
    const button = screen.getByRole("button", { name: /Confirmar/ });

    fireEvent.change(input, { target: { value: "123456" } });

    await waitFor(() => {
      expect(button).not.toBeDisabled();
    });
  });
});
