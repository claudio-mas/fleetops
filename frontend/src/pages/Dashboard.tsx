import { Link } from "react-router-dom";
import { useCurrentUser, useLogout } from "@/hooks/useAuth";

export function Dashboard() {
  const { data: user } = useCurrentUser();
  const { mutate: logout } = useLogout();

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
            <Link
              to="/mfa-setup"
              className="inline-block rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500"
            >
              Autenticação de Dois Fatores
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
