import type { PaletteMode } from "@mui/material";
import { dir } from "i18next";
import type { Metadata } from "next";
import { Mulish } from "next/font/google";
import { cookies } from "next/headers";
import "react-toastify/dist/ReactToastify.css";

import { languages } from "@/i18n/settings";

import { THEME_COOKIE_NAME } from "@/lib/constants";
import { getLocalizedMetadata } from "@/lib/metadata";
import AuthProvider from "@/lib/providers/AuthProvider";
import StoreProvider from "@/lib/providers/StoreProvider";
import ToastProvider from "@/lib/providers/ToastProvider";

import ThemeRegistry from "@/components/@mui/ThemeRegistry";

import "@/styles/globals.css";

const mulish = Mulish({
  subsets: ["latin"],
});

export async function generateMetadata({ params: { lng } }: { params: { lng: string } }): Promise<Metadata> {
  return getLocalizedMetadata(lng);
}

export async function generateStaticParams() {
  return languages.map((lng) => ({ lng }));
}

export default function RootLayout({
  children,
  params: { lng },
}: {
  children: React.ReactNode;
  params: { lng: string };
}) {
  const cookieStore = cookies();
  const theme = cookieStore.get(THEME_COOKIE_NAME)?.value as PaletteMode;
  return (
    <html lang={lng} dir={dir(lng)}>
      <body className={mulish.className}>
        <StoreProvider>
          <AuthProvider>
            <ThemeRegistry theme={theme}>
              <ToastProvider>{children} </ToastProvider>
            </ThemeRegistry>
          </AuthProvider>
        </StoreProvider>
      </body>
    </html>
  );
}
