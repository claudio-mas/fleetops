import { afterEach, beforeEach, describe, expect, test } from "vitest";
import type { AxiosError } from "axios";
import { handleResponseError } from "../../src/lib/api";

function makeError(status: number, url: string): AxiosError {
  return { response: { status }, config: { url } } as AxiosError;
}

describe("handleResponseError", () => {
  beforeEach(() => {
    localStorage.setItem("access_token", "a");
    localStorage.setItem("refresh_token", "r");
  });

  afterEach(() => {
    localStorage.clear();
  });

  test("does not clear tokens on 401 from the login endpoint", async () => {
    await expect(handleResponseError(makeError(401, "/v1/auth/login"))).rejects.toBeDefined();
    expect(localStorage.getItem("access_token")).toBe("a");
  });

  test("does not clear tokens on 401 from the mfa login endpoint", async () => {
    await expect(handleResponseError(makeError(401, "/v1/mfa/login"))).rejects.toBeDefined();
    expect(localStorage.getItem("access_token")).toBe("a");
  });

  test("clears tokens on 401 from a protected route", async () => {
    const original = window.location;
    Object.defineProperty(window, "location", {
      configurable: true,
      value: { ...original, href: "" },
    });

    await expect(handleResponseError(makeError(401, "/v1/auth/me"))).rejects.toBeDefined();
    expect(localStorage.getItem("access_token")).toBeNull();

    Object.defineProperty(window, "location", { configurable: true, value: original });
  });

  test("ignores non-401 errors", async () => {
    await expect(handleResponseError(makeError(500, "/v1/auth/me"))).rejects.toBeDefined();
    expect(localStorage.getItem("access_token")).toBe("a");
  });
});
