"use client";

import { useTheme } from "@mui/material";
import { signIn, useSession } from "next-auth/react";
import { redirect } from "next/navigation";
import { useEffect, useRef } from "react";

export default function Login() {
  const { status, data: session } = useSession();
  const theme = useTheme();
  const signInCalled = useRef(false);

  useEffect(() => {
    // Prevent multiple signIn calls
    if (signInCalled.current) return;

    if (status === "unauthenticated" || session?.error === "RefreshAccessTokenError") {
      signInCalled.current = true;

      const currentUrl = new URL(window.location.href);
      const searchParams = new URLSearchParams(currentUrl.search);
      const callbackUrlParam = searchParams.get("callbackUrl");
      const origin = currentUrl.origin;

      // Handle callbackUrl - it might be a full URL or just a path
      let callbackUrl = `${origin}/`;
      if (callbackUrlParam) {
        // Check if it's already a full URL
        if (callbackUrlParam.startsWith("http://") || callbackUrlParam.startsWith("https://")) {
          callbackUrl = callbackUrlParam;
        } else {
          // It's a relative path, prepend origin
          callbackUrl = `${origin}${callbackUrlParam.startsWith("/") ? "" : "/"}${callbackUrlParam}`;
        }
      }

      signIn(
        "keycloak",
        {
          callbackUrl,
        },
        {
          theme: theme.palette.mode,
        }
      );
    }
  }, [status, session?.error, theme.palette.mode]);

  if (session && session?.error !== "RefreshAccessTokenError") {
    redirect(`/`);
  }

  return <></>;
}
