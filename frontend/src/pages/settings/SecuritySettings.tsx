import { Link } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { useCurrentUser } from "@/hooks/useAuth";
import { useDisableMFA } from "@/hooks/useMFA";

export function SecuritySettings() {
  const { data: user } = useCurrentUser();
  const queryClient = useQueryClient();
  const { mutate: disableMFA, isPending: isDisabling } = useDisableMFA();

  const handleDisableMFA = () => {
    disableMFA(undefined, {
      onSuccess: () => queryClient.invalidateQueries({ queryKey: ["auth", "me"] }),
    });
  };

  return (
    <div className="max-w-2xl space-y-4">
      <div>
        <h2 className="text-lg font-semibold">Configurações de Segurança</h2>
        <p className="text-sm text-muted-foreground">
          Gerencie a autenticação de dois fatores da sua conta.
        </p>
      </div>
      {user &&
        (user.mfa_enabled ? (
          <div className="flex items-center gap-4">
            <span className="inline-flex items-center gap-2 text-sm font-medium text-green-700">
              <span aria-hidden>✓</span> Autenticação de dois fatores ativada
            </span>
            <Button variant="outline" size="sm" onClick={handleDisableMFA} disabled={isDisabling}>
              {isDisabling ? "Desativando..." : "Desativar"}
            </Button>
          </div>
        ) : (
          <Button asChild>
            <Link to="/mfa-setup">Ativar Autenticação de Dois Fatores</Link>
          </Button>
        ))}
    </div>
  );
}
