import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";

export const useVerifyEmail = () => {
  return useMutation({
    mutationFn: (token: string) =>
      api.post("/v1/email/verify", { token }).then((res) => res.data),
  });
};

export const useResendVerificationEmail = () => {
  return useMutation({
    mutationFn: () =>
      api.post("/v1/email/resend-verification", {}).then((res) => res.data),
  });
};
