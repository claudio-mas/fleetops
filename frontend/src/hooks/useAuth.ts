import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { useAuthStore } from "@/stores/auth";
import type {
  LoginRequest,
  MFALoginResponse,
  TenantRegistrationRequest,
  TokenResponse,
  UserRead,
} from "@/types/auth";

export function useCurrentUser() {
  const { isAuthenticated } = useAuthStore();
  return useQuery<UserRead>({
    queryKey: ["auth", "me"],
    queryFn: () => api.get<UserRead>("/v1/auth/me").then((r) => r.data),
    enabled: isAuthenticated(),
    staleTime: 5 * 60 * 1000,
  });
}

export function useLogin() {
  const { setTokens } = useAuthStore();
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  return useMutation<MFALoginResponse, Error, LoginRequest>({
    mutationFn: (data: LoginRequest) => {
      const form = new URLSearchParams();
      form.append("username", data.username);
      form.append("password", data.password);
      return api
        .post<MFALoginResponse>("/v1/auth/login", form, {
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
        })
        .then((r) => r.data);
    },
    onSuccess: (response) => {
      // Only navigate and set tokens if MFA is not required
      if (!response.mfa_required && response.access_token && response.refresh_token) {
        setTokens(response.access_token, response.refresh_token);
        queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
        navigate("/dashboard");
      }
      // If MFA is required, the component will handle showing the MFA form
    },
  });
}

export function useRegisterTenant() {
  const { setTokens } = useAuthStore();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: (data: TenantRegistrationRequest) =>
      api.post<TokenResponse>("/v1/auth/register", data).then((r) => r.data),
    onSuccess: (tokens) => {
      setTokens(tokens.access_token, tokens.refresh_token);
      navigate("/verify-email");
    },
  });
}

export function useLogout() {
  const { logout, accessToken } = useAuthStore();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () =>
      api.post("/v1/auth/logout", null, {
        headers: { Authorization: `Bearer ${accessToken}` },
      }),
    onSettled: () => {
      logout();
      queryClient.clear();
      navigate("/login");
    },
  });
}
