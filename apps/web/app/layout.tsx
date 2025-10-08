import { dir } from "i18next";
import type { Metadata } from "next";
import { getServerSession } from "next-auth";
import { Mulish } from "next/font/google";
import { cookies } from "next/headers";
import "react-toastify/dist/ReactToastify.css";

import { fallbackLng } from "@/i18n/settings";

import { LANGUAGE_COOKIE_NAME, THEME_COOKIE_NAME } from "@/lib/constants";
import { getLocalizedMetadata } from "@/lib/metadata";
import AuthProvider from "@/lib/providers/AuthProvider";
import { I18nProvider } from "@/lib/providers/I18nProvider";
// Providers and UI
import StoreProvider from "@/lib/providers/StoreProvider";
import ToastProvider from "@/lib/providers/ToastProvider";
import { SystemSettings } from "@/lib/validations/system";

import ThemeRegistry from "@/components/@mui/ThemeRegistry";

import { options } from "@/app/api/auth/[...nextauth]/options";
import "@/styles/globals.css";

// --- Metadata ---
export async function generateMetadata(): Promise<Metadata> {
  /** Try to use cookie first */
  const cookieStore = cookies();
  const lng = cookieStore.get(LANGUAGE_COOKIE_NAME)?.value ?? fallbackLng;
  return getLocalizedMetadata(lng);
}

const mulish = Mulish({
  subsets: ["latin"],
});

export const SYSTEM_API_BASE_URL = new URL("api/v2/system", process.env.NEXT_PUBLIC_API_URL).href;
const getSystemSettings = async (token: string): Promise<SystemSettings | null> => {
  if (!token) return null;
  try {
    const res = await fetch(`${SYSTEM_API_BASE_URL}/settings`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });
    if (!res.ok) return null;
    return (await res.json()) as SystemSettings;
  } catch (err) {
    console.error("getSystemSettings:", err);
    return null;
  }
};

// --- Layout ---
export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const serverCookies = cookies();
  let lang = serverCookies.get(LANGUAGE_COOKIE_NAME)?.value;
  let theme = serverCookies.get(THEME_COOKIE_NAME)?.value;
  if (!lang || !theme) {
    const session = await getServerSession(options);
    if (session?.access_token) {
      try {
        const prefs = await getSystemSettings(session.access_token);
        if (prefs) {
          lang = prefs.preferred_language ?? fallbackLng;
          theme = prefs.client_theme ?? "light";
        }
      } catch (err) {
        console.error("Failed to load prefs:", err);
      }
    }
    lang = lang ?? fallbackLng;
    theme = theme ?? "light";
  }
  return (
    <html lang={lang} dir={dir(lang)}>
      <body className={mulish.className}>
        <StoreProvider>
          <AuthProvider>
            <I18nProvider language={lang}>
              <ThemeRegistry theme={theme as "light" | "dark"}>
                <ToastProvider>{children}</ToastProvider>
              </ThemeRegistry>
            </I18nProvider>
          </AuthProvider>
        </StoreProvider>
      </body>
    </html>
  );
}
