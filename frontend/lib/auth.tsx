"use client";

import { createContext, useContext } from "react";

interface AuthContextValue {
  can: (permission: string) => boolean;
}

const AuthContext = createContext<AuthContextValue>({
  can: () => true,
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  return (
    <AuthContext.Provider value={{ can: () => true }}>{children}</AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  return useContext(AuthContext);
}
