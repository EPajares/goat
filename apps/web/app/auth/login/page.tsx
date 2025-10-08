"use client";

import { useTheme } from "@mui/material";
import { signIn, useSession } from "next-auth/react";
import { redirect } from "next/navigation";

export default function Login() {
  const { status, data: session } = useSession();
  const theme = useTheme();
  if (status === "unauthenticated" || session?.error === "RefreshAccessTokenError") {
    const currentUrl = new URL(window.location.href);
    const searchParams = new URLSearchParams(currentUrl.search);
    const path = searchParams.get("callbackUrl");
    const origin = currentUrl.origin;

    signIn(
      "keycloak",
      {
        callbackUrl: `${origin}${path ?? "/"}`,
      },
      {
        theme: theme.palette.mode,
      }
    );
  }
  if (session && session?.error !== "RefreshAccessTokenError") {
    redirect(`/`);
  }

  return <></>;
}
