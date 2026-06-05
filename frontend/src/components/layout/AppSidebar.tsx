import { ChevronDown, FolderCog, Home, LogOut, Settings, Truck } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
} from "@/components/ui/sidebar";
import { CADASTROS } from "@/config/cadastros";
import { useCurrentUser, useLogout } from "@/hooks/useAuth";

const cadastros = Object.values(CADASTROS);

export function AppSidebar() {
  const { pathname } = useLocation();
  const { data: user } = useCurrentUser();
  const { mutate: logout } = useLogout();

  const cadastrosOpen = pathname.startsWith("/cadastros");

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton asChild size="lg">
              <Link to="/dashboard">
                <Truck className="size-5" />
                <span className="text-base font-semibold">FleetOps</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarMenu>
            <SidebarMenuItem>
              <SidebarMenuButton asChild isActive={pathname === "/dashboard"} tooltip="Início">
                <Link to="/dashboard">
                  <Home />
                  <span>Início</span>
                </Link>
              </SidebarMenuButton>
            </SidebarMenuItem>

            <Collapsible defaultOpen={cadastrosOpen} className="group/collapsible">
              <SidebarMenuItem>
                <CollapsibleTrigger asChild>
                  <SidebarMenuButton tooltip="Cadastros">
                    <FolderCog />
                    <span>Cadastros</span>
                    <ChevronDown className="ml-auto transition-transform group-data-[state=open]/collapsible:rotate-180" />
                  </SidebarMenuButton>
                </CollapsibleTrigger>
                <CollapsibleContent>
                  <SidebarMenuSub>
                    {cadastros.map((c) => (
                      <SidebarMenuSubItem key={c.resource}>
                        <SidebarMenuSubButton
                          asChild
                          isActive={pathname === `/cadastros/${c.resource}`}
                        >
                          <Link to={`/cadastros/${c.resource}`}>{c.label}</Link>
                        </SidebarMenuSubButton>
                      </SidebarMenuSubItem>
                    ))}
                  </SidebarMenuSub>
                </CollapsibleContent>
              </SidebarMenuItem>
            </Collapsible>
          </SidebarMenu>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        <SidebarMenu>
          {user && (
            <SidebarMenuItem>
              <div className="truncate px-2 py-1 text-xs text-sidebar-foreground/70 group-data-[collapsible=icon]:hidden">
                {user.full_name}
              </div>
            </SidebarMenuItem>
          )}
          <SidebarMenuItem>
            <SidebarMenuButton
              asChild
              isActive={pathname.startsWith("/configuracoes")}
              tooltip="Configurações"
            >
              <Link to="/configuracoes/seguranca">
                <Settings />
                <span>Configurações</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
          <SidebarMenuItem>
            <SidebarMenuButton onClick={() => logout()} tooltip="Sair">
              <LogOut />
              <span>Sair</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}
