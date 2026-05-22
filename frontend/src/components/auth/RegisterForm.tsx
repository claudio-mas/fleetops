import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useRegisterTenant } from "@/hooks/useAuth";

const schema = z.object({
  razao_social: z.string().min(3, "Nome da empresa obrigatório"),
  cnpj: z.string().regex(/^\d{14}$/, "CNPJ deve ter 14 dígitos (somente números)"),
  admin_full_name: z.string().min(3, "Nome completo obrigatório"),
  admin_email: z.string().email("E-mail inválido"),
  admin_password: z.string().min(10, "Senha deve ter pelo menos 10 caracteres"),
});

type FormData = z.infer<typeof schema>;

export function RegisterForm() {
  const { mutate: register, isPending, error } = useRegisterTenant();

  const {
    register: field,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const fields: Array<{
    id: keyof FormData;
    label: string;
    type?: string;
    placeholder?: string;
  }> = [
    { id: "razao_social", label: "Razão Social", placeholder: "Empresa ABC Ltda" },
    { id: "cnpj", label: "CNPJ (14 dígitos)", placeholder: "12345678000190" },
    { id: "admin_full_name", label: "Seu nome completo" },
    { id: "admin_email", label: "E-mail corporativo", type: "email" },
    { id: "admin_password", label: "Senha", type: "password" },
  ];

  return (
    <form onSubmit={handleSubmit((data) => register(data))} className="space-y-4">
      {fields.map(({ id, label, type = "text", placeholder }) => (
        <div key={id}>
          <label htmlFor={id} className="block text-sm font-medium text-gray-700">
            {label}
          </label>
          <input
            id={id}
            type={type}
            placeholder={placeholder}
            {...field(id)}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
          {errors[id] && (
            <p className="mt-1 text-sm text-red-600">{errors[id]?.message}</p>
          )}
        </div>
      ))}

      {error && (
        <p className="text-sm text-red-600">
          {(error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
            "Erro ao criar conta. Verifique os dados."}
        </p>
      )}

      <button
        type="submit"
        disabled={isPending}
        className="w-full rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-indigo-500 disabled:opacity-60"
      >
        {isPending ? "Criando conta..." : "Criar conta grátis (7 dias trial)"}
      </button>
    </form>
  );
}
