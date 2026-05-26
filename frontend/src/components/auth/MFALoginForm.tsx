import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAuthStore } from "@/stores/auth";

const MFATokenSchema = z.object({
  token: z
    .string()
    .length(6, "Código deve ter exatamente 6 dígitos")
    .regex(/^\d+$/, "Apenas dígitos permitidos"),
});

type MFATokenInput = z.infer<typeof MFATokenSchema>;

interface MFALoginFormProps {
  challengeToken: string;
  onSuccess?: () => void;
}

export function MFALoginForm({ challengeToken, onSuccess }: MFALoginFormProps) {
  const navigate = useNavigate();
  const { setTokens } = useAuthStore();
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<MFATokenInput>({
    resolver: zodResolver(MFATokenSchema),
    defaultValues: { token: "" },
  });

  const tokenValue = watch("token");

  const mfaLoginMutation = useMutation({
    mutationFn: async (data: MFATokenInput) => {
      const response = await api.post<{ access_token: string; refresh_token: string }>(
        "/v1/mfa/login",
        { token: data.token },
        {
          headers: {
            "X-MFA-Challenge": challengeToken,
          },
        }
      );
      return response.data;
    },
    onSuccess: (data) => {
      setTokens(data.access_token, data.refresh_token);
      setError(null);
      if (onSuccess) {
        onSuccess();
      } else {
        navigate("/dashboard");
      }
    },
    onError: (err) => {
      const error = err as { response?: { data?: { detail?: string } } };
      const message =
        error.response?.data?.detail ||
        "Código TOTP inválido. Tente novamente.";
      setError(message);
    },
  });

  const onSubmit = (data: MFATokenInput) => {
    setError(null);
    mfaLoginMutation.mutate(data);
  };

  const handleTokenChange = (value: string) => {
    const sanitized = value.replace(/\D/g, "").slice(0, 6);
    setValue("token", sanitized);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">
          Verificação em duas etapas
        </h2>
        <p className="mt-2 text-sm text-gray-600">
          Digite o código de 6 dígitos do seu aplicativo autenticador.
        </p>
      </div>

      <div>
        <label htmlFor="token" className="block text-sm font-medium text-gray-700">
          Código TOTP
        </label>
        <input
          id="token"
          type="text"
          inputMode="numeric"
          placeholder="000000"
          maxLength={6}
          autoComplete="off"
          {...register("token")}
          onChange={(e) => {
            handleTokenChange(e.target.value);
          }}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-center text-2xl tracking-widest shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
        {errors.token && (
          <p className="mt-1 text-sm text-red-600">{errors.token.message}</p>
        )}
      </div>

      {error && (
        <div className="rounded-md bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <button
        type="submit"
        disabled={mfaLoginMutation.isPending || tokenValue.length !== 6}
        className="w-full rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-indigo-500 disabled:opacity-60"
      >
        {mfaLoginMutation.isPending ? "Verificando..." : "Confirmar"}
      </button>
    </form>
  );
}
