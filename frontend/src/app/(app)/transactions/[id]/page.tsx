"use client";

import { CheckCircle2, Clock3, Copy, XCircle } from "lucide-react";
import Link from "next/link";
import { use, useState } from "react";

import { Button, buttonVariants } from "@/components/ui/button";
import { useTransaction } from "@/hooks/use-transactions";
import { cn } from "@/lib/utils";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function TransactionDetailPage({ params }: PageProps) {
  const { id } = use(params);
  const tx = useTransaction(id);
  const [copied, setCopied] = useState(false);

  if (tx.isLoading) {
    return <p className="text-sm text-muted-foreground">Loading...</p>;
  }

  if (tx.isError || !tx.data) {
    return (
      <div className="mx-auto max-w-md py-12 text-center">
        <h2 className="text-2xl font-semibold tracking-tight">Not found</h2>
        <p className="mt-2 text-muted-foreground">
          This transaction doesn&apos;t exist or isn&apos;t yours.
        </p>
        <Link href="/buy" className={buttonVariants({ className: "mt-6 h-12 px-6 text-base" })}>
          Back to Buy
        </Link>
      </div>
    );
  }

  const data = tx.data;
  const expired = data.status === "pending" && new Date(data.expires_at).getTime() < Date.now();

  if (data.status === "paid" && data.token) {
    const tokenValue = data.token.value;
    return (
      <div className="mx-auto max-w-md">
        <StatusBadge tone="success" icon={<CheckCircle2 className="size-5" />}>
          Payment received
        </StatusBadge>
        <h1 className="mt-6 text-3xl font-bold tracking-tight">Here&apos;s your token</h1>
        <p className="mt-2 text-muted-foreground">
          Enter this on your meter to top up.
        </p>
        <div className="mt-6 rounded-xl border bg-muted/30 p-6 text-center">
          <p className="font-mono text-4xl font-semibold tracking-widest">{tokenValue}</p>
          <p className="mt-2 text-xs uppercase tracking-wider text-muted-foreground">
            Token
          </p>
        </div>
        <div className="mt-4 flex items-center justify-between text-sm text-muted-foreground">
          <span>Control number</span>
          <span className="font-mono text-foreground">{data.control_number}</span>
        </div>
        <Button
          variant="outline"
          className="mt-6 h-11 w-full"
          onClick={() => {
            navigator.clipboard.writeText(tokenValue);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
          }}
        >
          <Copy className="mr-2 size-4" />
          {copied ? "Copied" : "Copy token"}
        </Button>
      </div>
    );
  }

  if (data.status === "failed" || expired) {
    return (
      <div className="mx-auto max-w-md py-4">
        <StatusBadge tone="destructive" icon={<XCircle className="size-5" />}>
          {expired ? "Expired" : "Payment failed"}
        </StatusBadge>
        <h1 className="mt-6 text-3xl font-bold tracking-tight">
          {expired ? "This control number expired" : "Something went wrong"}
        </h1>
        <p className="mt-2 text-muted-foreground">
          {expired
            ? "Payment didn't arrive in time. You can start a new top-up."
            : "The payment provider reported a failure. Try again."}
        </p>
        <Link href="/buy" className={buttonVariants({ size: "lg", className: "mt-6 h-12 px-6 text-base" })}>
          Try again
        </Link>
      </div>
    );
  }

  // pending
  return (
    <div className="mx-auto max-w-md py-4">
      <StatusBadge tone="info" icon={<Clock3 className="size-5 animate-pulse" />}>
        Waiting for payment
      </StatusBadge>
      <h1 className="mt-6 text-3xl font-bold tracking-tight">Pay this control number</h1>
      <p className="mt-2 text-muted-foreground">
        Use M-Pesa, Tigo Pesa, or your bank. This page updates automatically.
      </p>
      <div className="mt-6 rounded-xl border bg-muted/30 p-6 text-center">
        <p className="font-mono text-3xl font-semibold tracking-widest">{data.control_number}</p>
        <p className="mt-2 text-xs uppercase tracking-wider text-muted-foreground">
          Control number
        </p>
      </div>
      <div className="mt-4 flex items-center justify-between rounded-lg border bg-white px-4 py-3 text-sm">
        <span className="text-muted-foreground">Amount</span>
        <span className="font-semibold">TZS {data.amount}</span>
      </div>
    </div>
  );
}

function StatusBadge({
  tone,
  icon,
  children,
}: {
  tone: "success" | "destructive" | "info";
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 rounded-full px-3 py-1 text-sm font-medium",
        tone === "success" && "bg-emerald-500/10 text-emerald-700",
        tone === "destructive" && "bg-destructive/10 text-destructive",
        tone === "info" && "bg-primary/10 text-primary",
      )}
    >
      {icon}
      {children}
    </span>
  );
}
