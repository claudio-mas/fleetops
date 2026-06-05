import { describe, expect, it } from "vitest";
import { CADASTROS, getCadastro } from "@/config/cadastros";

describe("config cadastros", () => {
  it("registra as 11 entidades", () => {
    expect(Object.keys(CADASTROS)).toHaveLength(11);
  });

  it("cada entidade tem label, resource e ao menos um campo", () => {
    for (const c of Object.values(CADASTROS)) {
      expect(c.label.length).toBeGreaterThan(0);
      expect(c.resource.length).toBeGreaterThan(0);
      expect(c.fields.length).toBeGreaterThan(0);
    }
  });

  it("resolve config por slug", () => {
    expect(getCadastro("centro-custo")?.label).toBe("Centros de Custo");
    expect(getCadastro("inexistente")).toBeUndefined();
  });
});
