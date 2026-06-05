import { useCurrentUser } from "@/hooks/useAuth";

export function Home() {
  const { data: user } = useCurrentUser();
  return (
    <div className="space-y-2">
      <h2 className="text-2xl font-bold">Bem-vindo{user ? `, ${user.full_name}` : ""}!</h2>
      <p className="text-muted-foreground">
        Use o menu lateral para navegar entre os cadastros e configurações.
      </p>
    </div>
  );
}
