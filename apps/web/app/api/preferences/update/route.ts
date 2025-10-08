import { NextResponse } from "next/server";
import { fallbackLng } from "@/i18n/settings";
import { LANGUAGE_COOKIE_NAME, THEME_COOKIE_NAME } from "@/lib/constants";

export const runtime = "nodejs";

export const POST = async (req: Request) => {
    const { lang, theme } = (await req.json()) as { lang?: string; theme?: string };
    const res = NextResponse.json({ success: true });
    const TEN_MINUTES = 60 * 10;

    res.cookies.set(LANGUAGE_COOKIE_NAME, lang ?? fallbackLng, {
        path: "/",
        maxAge: TEN_MINUTES,
        sameSite: "lax",
        secure: process.env.NODE_ENV === "production",
    });
    res.cookies.set(THEME_COOKIE_NAME, theme ?? "light", {
        path: "/",
        maxAge: TEN_MINUTES,
        sameSite: "lax",
        secure: process.env.NODE_ENV === "production",
    });

    return res;
};