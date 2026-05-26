import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";

interface MFASetupResponse {
  secret: string;
  qr_code: string;
  message: string;
}

interface MFAConfirmRequest {
  secret: string;
  token: string;
}

export const useSetupMFA = () => {
  return useMutation<MFASetupResponse>({
    mutationFn: () =>
      api.post<MFASetupResponse>("/v1/mfa/setup", {}).then((res) => res.data),
  });
};

export const useConfirmMFA = () => {
  return useMutation({
    mutationFn: (data: MFAConfirmRequest) =>
      api.post("/v1/mfa/confirm", data).then((res) => res.data),
  });
};

export const useDisableMFA = () => {
  return useMutation({
    mutationFn: () =>
      api.post("/v1/mfa/disable", {}).then((res) => res.data),
  });
};
