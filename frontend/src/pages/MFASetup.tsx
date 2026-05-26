import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useSetupMFA, useConfirmMFA } from "@/hooks/useMFA";
import { useMFAStore } from "@/stores/mfa";

interface ApiError {
  response?: {
    data?: {
      detail?: string;
    };
  };
}

export default function MFASetup() {
  const navigate = useNavigate();
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const setupMutation = useSetupMFA();
  const confirmMutation = useConfirmMFA();

  const { secret, qrCode, setSecret } = useMFAStore();

  useEffect(() => {
    if (!secret && !setupMutation.isPending) {
      setupMutation.mutate(undefined, {
        onSuccess: (data) => {
          setSecret(data.secret, data.qr_code);
        },
        onError: (err: unknown) => {
          const error = err as ApiError;
          setError(error.response?.data?.detail || "Falha ao gerar QR code");
        },
      });
    }
  }, [secret, setupMutation, setSecret]);

  const handleConfirm = () => {
    if (!secret || !code) {
      setError("Código TOTP de 6 dígitos é obrigatório");
      return;
    }

    if (code.length !== 6 || !/^\d+$/.test(code)) {
      setError("Código deve conter exatamente 6 dígitos");
      return;
    }

    confirmMutation.mutate(
      { secret, token: code },
      {
        onSuccess: () => {
          setMessage("MFA habilitado com sucesso!");
          setTimeout(() => {
            navigate("/dashboard");
          }, 2000);
        },
        onError: (err: unknown) => {
          const error = err as ApiError;
          setError(error.response?.data?.detail || "Código inválido ou expirado");
        },
      }
    );
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8">
        <div>
          <h1 className="mt-6 text-center text-3xl font-bold tracking-tight text-gray-900">
            Ativar Autenticação de Dois Fatores
          </h1>
        </div>

        <div className="space-y-6">
          {error && (
            <div className="rounded-md bg-red-50 border border-red-200 p-4">
              <p className="text-red-800 text-sm">{error}</p>
            </div>
          )}

          {message && (
            <div className="rounded-md bg-green-50 border border-green-200 p-4">
              <p className="text-green-800 text-sm">{message}</p>
            </div>
          )}

          {qrCode && !message && (
            <>
              <div className="bg-white p-6 rounded-lg border border-gray-200">
                <div className="text-center">
                  <img src={qrCode} alt="QR Code" className="w-48 h-48 mx-auto" />
                </div>
              </div>

              <div className="bg-yellow-50 border border-yellow-200 p-4 rounded">
                <p className="font-semibold text-yellow-900 mb-3">Instruções:</p>
                <ol className="text-sm text-yellow-800 space-y-2">
                  <li className="flex">
                    <span className="font-bold mr-2">1.</span>
                    <span>Baixe um aplicativo autenticador:</span>
                  </li>
                  <li className="ml-6 text-xs text-gray-600">
                    • Google Authenticator (iOS/Android)
                  </li>
                  <li className="ml-6 text-xs text-gray-600">
                    • Microsoft Authenticator (iOS/Android)
                  </li>
                  <li className="ml-6 text-xs text-gray-600">• Authy (iOS/Android)</li>

                  <li className="flex mt-4">
                    <span className="font-bold mr-2">2.</span>
                    <span>Abra o aplicativo e escaneie o QR code acima</span>
                  </li>

                  <li className="flex">
                    <span className="font-bold mr-2">3.</span>
                    <span>Digite o código de 6 dígitos abaixo</span>
                  </li>
                </ol>
              </div>

              <div className="space-y-3">
                <input
                  type="text"
                  placeholder="000000"
                  maxLength={6}
                  value={code}
                  onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
                  className="w-full text-center text-3xl tracking-widest font-mono px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />

                <button
                  onClick={handleConfirm}
                  disabled={confirmMutation.isPending || code.length !== 6}
                  className="w-full rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-indigo-500 disabled:opacity-60"
                >
                  {confirmMutation.isPending ? "Confirmando..." : "Confirmar"}
                </button>
              </div>
            </>
          )}

          {setupMutation.isPending && !qrCode && (
            <div className="text-center">
              <p className="text-gray-600">Gerando QR code...</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
