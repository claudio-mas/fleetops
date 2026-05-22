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
        <p className="mt-4 text-gray-600">
          Bem-vindo, <strong>{user.full_name}</strong>!
        </p>
      )}
    </div>
  );
}
