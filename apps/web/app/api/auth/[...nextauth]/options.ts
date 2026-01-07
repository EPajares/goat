import type { KeycloakTokenSet, NextAuthOptions } from "next-auth";
import type { JWT } from "next-auth/jwt";
import KeycloakProvider from "next-auth/providers/keycloak";

const keycloak = KeycloakProvider({
  id: "keycloak",
  clientId: process.env.NEXT_PUBLIC_KEYCLOAK_CLIENT_ID as string,
  clientSecret: process.env.KEYCLOAK_CLIENT_SECRET as string,
  issuer: process.env.NEXT_PUBLIC_KEYCLOAK_ISSUER,
  authorization: { params: { scope: "openid email profile offline_access" } },
});

// this performs the final handshake for the keycloak provider
export async function doFinalSignoutHandshake(token: JWT) {
  if (token.provider == keycloak.id) {
    try {
      const issuerUrl = keycloak.options?.issuer;
      const logOutUrl = new URL(`${issuerUrl}/protocol/openid-connect/logout`);
      logOutUrl.searchParams.set("id_token_hint", token.id_token);
      const { status, statusText } = await fetch(logOutUrl);
      console.log("Completed post-logout handshake", status, statusText);
    } catch {
      console.error("Unable to perform post-logout handshake");
    }
  }
}

export async function refreshAccessToken(token: JWT): Promise<JWT> {
  try {
    const response = await fetch(`${keycloak.options?.issuer}/protocol/openid-connect/token`, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        client_id: keycloak.options?.clientId as string,
        client_secret: keycloak.options?.clientSecret as string,
        grant_type: "refresh_token",
        refresh_token: token.refresh_token as string,
      }),
      method: "POST",
    });

    const tokensRaw = await response.json();
    const tokens: KeycloakTokenSet = tokensRaw;
    if (!response.ok) throw tokens;

    const expiresAt = Math.floor(Date.now() / 1000 + tokens.expires_in);
    console.log(`Token was refreshed. New token expires in ${tokens.expires_in} sec at ${expiresAt}`);
    const newToken: JWT = {
      ...token,
      access_token: tokens.access_token,
      expires_at: expiresAt,
      refresh_token: tokens.refresh_token ?? token.refresh_token,
      id_token: tokens.id_token ?? token.id_token,
      provider: keycloak.id,
    };
    return newToken;
  } catch (error) {
    console.error("Error refreshing access token: ", error);
    return {
      ...token,
      error: "RefreshAccessTokenError",
    };
  }
}

export const options: NextAuthOptions = {
  secret: process.env.NEXTAUTH_SECRET,
  providers: [keycloak],
  callbacks: {
    async session({ session, token }) {
      if (token) {
        session.access_token = token.access_token;
        session.error = token.error;
      }
      return session;
    },
    async jwt({ token, account, user }) {
      if (account && user) {
        if (!account.access_token) throw Error("Auth Provider missing access token");
        if (!account.refresh_token) throw Error("Auth Provider missing refresh token");
        if (!account.id_token) throw Error("Auth Provider missing ID token");
        const newToken: JWT = {
          ...token,
          access_token: account.access_token,
          refresh_token: account.refresh_token,
          id_token: account.id_token,
          expires_at: Math.floor(account.expires_at ?? 0),
          provider: account.provider,
        };

        return newToken;
      }
      if (Date.now() < token.expires_at * 1000) {
        return token;
      }
      const newToken = await refreshAccessToken(token);
      return newToken;
    },
  },
  events: {
    signOut: async ({ token }) => doFinalSignoutHandshake(token),
  },
  jwt: {
    maxAge: 1 * 60, // 1 minute, same as in Keycloak
  },
  pages: {
    signIn: "/auth/login",
  },
  session: {
    strategy: "jwt",
    maxAge: 30 * 24 * 60 * 60, // 30 days : 2592000, same as in Keycloak
  },
};
