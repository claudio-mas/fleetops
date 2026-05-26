import { create } from "zustand";

interface MFAState {
  secret: string | null;
  qrCode: string | null;
  mfaEnabled: boolean;
  setSecret: (secret: string, qrCode: string) => void;
  clearSecret: () => void;
  setMFAEnabled: (enabled: boolean) => void;
}

export const useMFAStore = create<MFAState>((set) => ({
  secret: null,
  qrCode: null,
  mfaEnabled: false,
  setSecret: (secret, qrCode) => set({ secret, qrCode }),
  clearSecret: () => set({ secret: null, qrCode: null }),
  setMFAEnabled: (enabled) => set({ mfaEnabled: enabled }),
}));
