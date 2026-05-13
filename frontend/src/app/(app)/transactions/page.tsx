"use client";

import Link from "next/link";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useTransactions } from "@/hooks/use-transactions";
import type { TransactionStatus } from "@/types/api";

const STATUS_LABEL: Record<TransactionStatus, string> = {
  pending: "Pending",
  paid: "Paid",
  expired: "Expired",
  failed: "Failed",
};

export default function TransactionsPage() {
  const txs = useTransactions();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Transactions</CardTitle>
      </CardHeader>
      <CardContent>
        {txs.isLoading && <p className="text-sm text-muted-foreground">Loading...</p>}
        {txs.data && txs.data.length === 0 && (
          <p className="text-sm text-muted-foreground">No transactions yet.</p>
        )}
        {txs.data && txs.data.length > 0 && (
          <ul className="divide-y">
            {txs.data.map((tx) => (
              <li key={tx.id} className="py-3">
                <Link
                  href={`/transactions/${tx.id}`}
                  className="flex items-center justify-between hover:underline"
                >
                  <div>
                    <p className="font-mono">{tx.control_number}</p>
                    <p className="text-sm text-muted-foreground">
                      TZS {tx.amount} · {new Date(tx.created_at).toLocaleString()}
                    </p>
                  </div>
                  <span className="text-sm">{STATUS_LABEL[tx.status]}</span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
