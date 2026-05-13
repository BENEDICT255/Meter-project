"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import { api } from "@/lib/api";
import { clearTokens, saveTokenPair } from "@/lib/auth";
import type { TokenPair, User } from "@/types/api";

interface LoginInput {
  phone_number: string;
  password: string;
}

interface RegisterInput {
  phone_number: string;
  password: string;
  email?: string;
}

export function useLogin() {
  const router = useRouter();
  return useMutation({
    mutationFn: async (input: LoginInput) => {
      const resp = await api.post<TokenPair>("/auth/login/", input);
      return resp.data;
    },
    onSuccess: (pair) => {
      saveTokenPair(pair);
      router.push("/buy");
    },
  });
}

export function useRegister() {
  const router = useRouter();
  return useMutation({
    mutationFn: async (input: RegisterInput) => {
      await api.post("/auth/register/", input);
      // Auto-login after register
      const loginResp = await api.post<TokenPair>("/auth/login/", {
        phone_number: input.phone_number,
        password: input.password,
      });
      return loginResp.data;
    },
    onSuccess: (pair) => {
      saveTokenPair(pair);
      router.push("/buy");
    },
  });
}

export function useMe() {
  return useQuery({
    queryKey: ["me"],
    queryFn: async () => {
      const resp = await api.get<User>("/auth/me/");
      return resp.data;
    },
  });
}

export function useLogout() {
  const router = useRouter();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      try {
        await api.post("/auth/logout/", {});
      } catch {
        // Stub endpoint may return non-2xx; ignore.
      }
    },
    onSettled: () => {
      clearTokens();
      qc.clear();
      router.push("/login");
    },
  });
}
