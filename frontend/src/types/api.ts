export interface User {
  id: string;
  phone_number: string;
  email: string | null;
  date_joined: string;
}

export interface Meter {
  id: string;
  meter_number: string;
  label: string;
  created_at: string;
}

export type TransactionStatus = "pending" | "paid" | "expired" | "failed";

export interface Token {
  id: string;
  value: string;
  strategy: string;
  delivered_via_sms: boolean;
  delivered_at: string | null;
  created_at: string;
}

export interface Transaction {
  id: string;
  meter: string;
  amount: string;
  control_number: string;
  status: TransactionStatus;
  provider_reference: string;
  paid_at: string | null;
  expires_at: string;
  created_at: string;
  token: Token | null;
}

export interface TokenPair {
  access: string;
  refresh: string;
}
