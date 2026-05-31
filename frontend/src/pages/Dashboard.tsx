import { Link } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { useCurrentUser, useLogout } from "@/hooks/useAuth";
import { useDisableMFA } from "@/hooks/useMFA";

export function Dashboard() {
  const { data: user } = useCurrentUser();
  const { mutate: logout } = useLogout();
  const queryClient = useQueryClient();
  const { mutate: disableMFA, isPending: isDisabling } = useDisableMFA();

  const handleDisableMFA = () => {
    disableMFA(undefined, {
      onSuccess: () => queryClient.invalidateQueries({ queryKey: ["auth", "me"] }),
    });
  };

  return (
    <div className="p-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <button
          onClick={() => logout()}
          className="rounded-md bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-500"
        >
          Sair
        </button>
      </div>
      {user && (
        <div className="mt-4 space-y-4">
          <p className="text-gray-600">
            Bem-vindo, <strong>{user.full_name}</strong>!
          </p>
          <div className="pt-4 border-t border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">Configurações de Segurança</h2>
            {user.mfa_enabled ? (
              <div className="flex items-center gap-4">
                <span className="inline-flex items-center gap-2 text-sm font-medium text-green-700">
                  <span aria-hidden>✓</span> Autenticação de dois fatores ativada
                </span>
                <button
                  onClick={handleDisableMFA}
                  disabled={isDisabling}
                  className="rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-60"
                >
                  {isDisabling ? "Desativando..." : "Desativar"}
                </button>
              </div>
            ) : (
              <Link
                to="/mfa-setup"
                className="inline-block rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500"
              >
                Ativar Autenticação de Dois Fatores
              </Link>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
