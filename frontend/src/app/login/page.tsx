"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Droplets } from "lucide-react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { useLogin } from "@/hooks/use-auth";
import { getApiErrorMessage } from "@/lib/api";

const schema = z.object({
  phone_number: z.string().min(8, "Phone number is required"),
  password: z.string().min(1, "Password is required"),
});

type Values = z.infer<typeof schema>;

export default function LoginPage() {
  const form = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: { phone_number: "", password: "" },
  });
  const login = useLogin();

  const onSubmit = (values: Values) => {
    login.mutate(values, {
      onError: (err) => {
        form.setError("root", { message: getApiErrorMessage(err) });
      },
    });
  };

  return (
    <main className="flex min-h-screen flex-col bg-white">
      <header className="px-8 py-6">
        <div className="flex items-center gap-2 text-foreground">
          <Droplets className="size-6 text-primary" />
          <span className="text-lg font-semibold tracking-tight">Daraja Water</span>
        </div>
      </header>
      <div className="flex flex-1 items-center justify-center px-6 pb-16">
        <div className="w-full max-w-md space-y-8">
          <div className="space-y-2">
            <h1 className="text-3xl font-bold tracking-tight">Welcome back</h1>
            <p className="text-muted-foreground">Sign in with your phone number to top up.</p>
          </div>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
              <FormField
                control={form.control}
                name="phone_number"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Phone number</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="+255700000000"
                        className="h-12 text-base"
                        inputMode="tel"
                        autoComplete="tel"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Password</FormLabel>
                    <FormControl>
                      <Input
                        type="password"
                        className="h-12 text-base"
                        autoComplete="current-password"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              {form.formState.errors.root && (
                <div className="rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
                  {form.formState.errors.root.message}
                </div>
              )}
              <Button
                type="submit"
                size="lg"
                disabled={login.isPending}
                className="h-12 w-full text-base"
              >
                {login.isPending ? "Signing in..." : "Sign in"}
              </Button>
              <p className="text-center text-sm text-muted-foreground">
                No account?{" "}
                <Link href="/register" className="font-medium text-primary hover:underline">
                  Create one
                </Link>
              </p>
            </form>
          </Form>
        </div>
      </div>
    </main>
  );
}
