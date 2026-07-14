"use client";

import Link from "next/link";

import { useTransactions } from "@/hooks/use-transactions";
import { cn } from "@/lib/utils";
import type { TransactionStatus } from "@/types/api";

const STATUS_LABEL: Record<TransactionStatus, string> = {
  pending: "Pending",
  paid: "Paid",
  expired: "Expired",
  failed: "Failed",
};

const STATUS_TONE: Record<TransactionStatus, string> = {
  pending: "bg-primary/10 text-primary",
  paid: "bg-emerald-500/10 text-emerald-700",
  expired: "bg-muted text-muted-foreground",
  failed: "bg-destructive/10 text-destructive",
};

export default function TransactionsPage() {
  const txs = useTransactions();

  return (
    <div className="mx-auto max-w-2xl">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">History</h1>
        <p className="text-muted-foreground">Your recent top-ups, newest first.</p>
      </div>
      <div className="mt-8 overflow-hidden rounded-xl border bg-white">
        {txs.isLoading && (
          <p className="px-6 py-12 text-center text-sm text-muted-foreground">Loading...</p>
        )}
        {txs.data && txs.data.length === 0 && (
          <p className="px-6 py-12 text-center text-sm text-muted-foreground">
            No transactions yet.
          </p>
        )}
        {txs.data && txs.data.length > 0 && (
          <ul className="divide-y">
            {txs.data.map((tx) => (
              <li key={tx.id}>
                <Link
                  href={`/transactions/${tx.id}`}
                  className="flex items-center justify-between px-5 py-4 transition-colors hover:bg-muted/40"
                >
                  <div className="min-w-0">
                    <p className="font-mono text-sm">
                      {tx.token
                        ? `Token: ${tx.token.value}`
                        : tx.control_number}
                    </p>
                    <p className="mt-0.5 text-xs text-muted-foreground">
                      {new Date(tx.created_at).toLocaleString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="font-semibold tabular-nums">TZS {tx.amount}</span>
                    <span
                      className={cn(
                        "rounded-full px-2.5 py-0.5 text-xs font-medium",
                        STATUS_TONE[tx.status],
                      )}
                    >
                      {STATUS_LABEL[tx.status]}
                    </span>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
