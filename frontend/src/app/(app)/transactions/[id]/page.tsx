"use client";

import Link from "next/link";
import { use } from "react";

import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useTransaction } from "@/hooks/use-transactions";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function TransactionDetailPage({ params }: PageProps) {
  const { id } = use(params);
  const tx = useTransaction(id);

  if (tx.isLoading) {
    return <p className="text-sm text-muted-foreground">Loading...</p>;
  }

  if (tx.isError || !tx.data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Not found</CardTitle>
        </CardHeader>
        <CardContent>
          <p>This transaction doesn&apos;t exist or isn&apos;t yours.</p>
          <Link href="/buy" className={buttonVariants({ className: "mt-4" })}>
            Back to Buy
          </Link>
        </CardContent>
      </Card>
    );
  }

  const data = tx.data;
  const expired = data.status === "pending" && new Date(data.expires_at).getTime() < Date.now();

  if (data.status === "paid" && data.token) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>✓ Payment received</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <p className="text-sm text-muted-foreground">Your token</p>
            <p className="mt-1 font-mono text-3xl tracking-wider">{data.token.value}</p>
          </div>
          <p className="text-sm text-muted-foreground">
            Enter the token on your meter. Control number:{" "}
            <span className="font-mono">{data.control_number}</span>
          </p>
          <Button
            variant="outline"
            onClick={() => {
              if (data.token) navigator.clipboard.writeText(data.token.value);
            }}
          >
            Copy token
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (data.status === "failed" || expired) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{expired ? "Expired" : "Payment failed"}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            {expired
              ? "This control number expired before payment was received."
              : "The payment provider reported a failure."}
          </p>
          <Link href="/buy" className={buttonVariants()}>
            Try again
          </Link>
        </CardContent>
      </Card>
    );
  }

  // pending
  return (
    <Card>
      <CardHeader>
        <CardTitle>Waiting for payment...</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <p className="text-sm text-muted-foreground">Control number</p>
          <p className="mt-1 font-mono text-2xl">{data.control_number}</p>
        </div>
        <div>
          <p className="text-sm text-muted-foreground">Amount</p>
          <p className="text-lg">TZS {data.amount}</p>
        </div>
        <p className="text-sm text-muted-foreground">
          Pay this control number via M-Pesa, Tigo Pesa, or your bank.
          This page will update automatically once payment is received.
        </p>
      </CardContent>
    </Card>
  );
}
