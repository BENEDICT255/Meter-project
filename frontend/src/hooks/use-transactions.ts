"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { Transaction } from "@/types/api";

const LIST_KEY = ["transactions"] as const;
const DETAIL_KEY = (id: string) => ["transactions", id] as const;

export function useTransactions() {
  return useQuery({
    queryKey: LIST_KEY,
    queryFn: async () => {
      const resp = await api.get<Transaction[]>("/transactions/");
      return resp.data;
    },
  });
}

export function useTransaction(id: string) {
  return useQuery({
    queryKey: DETAIL_KEY(id),
    queryFn: async () => {
      const resp = await api.get<Transaction>(`/transactions/${id}/`);
      return resp.data;
    },
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return 2000;
      if (data.status !== "pending") return false;
      if (new Date(data.expires_at).getTime() < Date.now()) return false;
      return 2000;
    },
  });
}

interface InitiateInput {
  meter_id: string;
  amount: string;
}

export function useInitiateTransaction() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (input: InitiateInput) => {
      const resp = await api.post<Transaction>("/transactions/initiate/", input);
      return resp.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: LIST_KEY });
    },
  });
}
