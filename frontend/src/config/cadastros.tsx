export type FieldType = "text" | "number" | "money" | "textarea" | "ref";

export interface FieldConfig {
  name: string;
  label: string;
  type: FieldType;
  required?: boolean;
  refResource?: string; // para type "ref": slug do recurso referenciado
  listColumn?: boolean; // exibir na tabela de listagem
}

export interface CadastroConfig {
  resource: string; // slug usado na URL/endpoint
  label: string; // título plural
  singular: string;
  fields: FieldConfig[];
}

const text = (name: string, label: string, required = false, listColumn = false): FieldConfig => ({
  name,
  label,
  type: "text",
  required,
  listColumn,
});

const NOME = text("nome", "Nome", true, true);
const OBS: FieldConfig = { name: "observacoes", label: "Observações", type: "textarea" };

export const CADASTROS: Record<string, CadastroConfig> = {
  "centro-custo": {
    resource: "centro-custo",
    label: "Centros de Custo",
    singular: "Centro de Custo",
    fields: [NOME, text("responsavel", "Responsável", false, true), OBS],
  },
  "conta-contabil": {
    resource: "conta-contabil",
    label: "Contas Contábeis",
    singular: "Conta Contábil",
    fields: [NOME, text("grupo", "Grupo", false, true), OBS],
  },
  cargo: {
    resource: "cargo",
    label: "Cargos",
    singular: "Cargo",
    fields: [NOME, { name: "salario", label: "Salário", type: "money", listColumn: true }, OBS],
  },
  colaborador: {
    resource: "colaborador",
    label: "Colaboradores",
    singular: "Colaborador",
    fields: [
      NOME,
      { name: "cargo_id", label: "Cargo", type: "ref", refResource: "cargo", listColumn: true },
      text("telefone", "Telefone"),
      text("email", "E-mail", false, true),
      OBS,
    ],
  },
  fornecedor: {
    resource: "fornecedor",
    label: "Fornecedores",
    singular: "Fornecedor",
    fields: [
      NOME,
      text("tipo", "Tipo (PF/PJ)"),
      text("cnpj_cpf", "CNPJ/CPF", false, true),
      text("rg_ie", "RG/IE"),
      text("endereco", "Endereço"),
      text("bairro", "Bairro"),
      text("cep", "CEP"),
      text("cidade", "Cidade", false, true),
      text("uf", "UF"),
      text("telefone", "Telefone"),
      text("email", "E-mail"),
      OBS,
    ],
  },
  combustivel: {
    resource: "combustivel",
    label: "Combustíveis",
    singular: "Combustível",
    fields: [NOME, OBS],
  },
  "tipo-equipamento": {
    resource: "tipo-equipamento",
    label: "Tipos de Equipamento",
    singular: "Tipo de Equipamento",
    fields: [
      NOME,
      {
        name: "depreciacao_anual",
        label: "Depreciação anual (%)",
        type: "number",
        listColumn: true,
      },
      OBS,
    ],
  },
  "tipo-servico": {
    resource: "tipo-servico",
    label: "Tipos de Serviço",
    singular: "Tipo de Serviço",
    fields: [NOME, OBS],
  },
  "grupo-insumo": {
    resource: "grupo-insumo",
    label: "Grupos de Insumo",
    singular: "Grupo de Insumo",
    fields: [NOME, OBS],
  },
  "unidade-medida": {
    resource: "unidade-medida",
    label: "Unidades de Medida",
    singular: "Unidade de Medida",
    fields: [text("codigo", "Código", true, true), NOME, OBS],
  },
  insumo: {
    resource: "insumo",
    label: "Insumos",
    singular: "Insumo",
    fields: [
      NOME,
      {
        name: "grupo_insumo_id",
        label: "Grupo",
        type: "ref",
        refResource: "grupo-insumo",
        listColumn: true,
      },
      {
        name: "unidade_medida_id",
        label: "Unidade",
        type: "ref",
        refResource: "unidade-medida",
        listColumn: true,
      },
      { name: "preco_medio", label: "Preço médio", type: "money", listColumn: true },
      text("marca", "Marca"),
      text("fabricante", "Fabricante"),
      OBS,
    ],
  },
};

export function getCadastro(slug: string): CadastroConfig | undefined {
  return CADASTROS[slug];
}
