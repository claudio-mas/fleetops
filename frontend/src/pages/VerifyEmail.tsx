import { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { useVerifyEmail, useResendVerificationEmail } from "@/hooks/useEmailVerification";

export default function VerifyEmail() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get("token");

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const verifyMutation = useVerifyEmail();
  const resendMutation = useResendVerificationEmail();

  useEffect(() => {
    if (token) {
      verifyMutation.mutate(token, {
        onSuccess: () => {
          setMessage("Email verificado com sucesso! Redirecionando...");
          setTimeout(() => navigate("/dashboard"), 2000);
        },
        onError: (err) => {
          const errorMessage =
            (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
            "Falha ao verificar e-mail";
          setError(errorMessage);
        },
      });
    }
  }, [token, navigate, verifyMutation]);

  const handleResend = () => {
    setError("");
    setMessage("");
    resendMutation.mutate(undefined, {
      onSuccess: () => setMessage("Novo link de verificação enviado para seu e-mail"),
      onError: (err) => {
        const errorMessage =
          (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
          "Falha ao reenviar link";
        setError(errorMessage);
      },
    });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8">
        <div>
          <h1 className="mt-6 text-center text-3xl font-bold tracking-tight text-gray-900">
            Verificar E-mail
          </h1>
        </div>

        <div className="space-y-4">
          {message && (
            <div className="rounded-md bg-green-50 border border-green-200 p-4">
              <p className="text-green-800 text-sm">{message}</p>
            </div>
          )}

          {error && (
            <div className="rounded-md bg-red-50 border border-red-200 p-4">
              <p className="text-red-800 text-sm">{error}</p>
            </div>
          )}

          {!message && (
            <>
              <p className="text-center text-sm text-gray-600">
                Enviamos um link de confirmação para seu e-mail. Clique no link ou use o botão
                abaixo para reenviar.
              </p>

              <button
                onClick={handleResend}
                disabled={resendMutation.isPending}
                className="w-full rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-indigo-500 disabled:opacity-60"
              >
                {resendMutation.isPending ? "Enviando..." : "Reenviar Link"}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
