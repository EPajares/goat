import { NextResponse } from "next/server";
import type { NextFetchEvent, NextMiddleware, NextRequest } from "next/server";

import type { MiddlewareFactory } from "@/middlewares/types";

const SUPPORTED_LOCALES = ["en", "de"];

export const withLegacyRedirect: MiddlewareFactory = (next: NextMiddleware) => {
    return async (request: NextRequest, _next: NextFetchEvent) => {
        const { pathname, origin } = request.nextUrl;
        const segments = pathname.split("/");          // ['', 'en', 'home', ...]
        const maybeLocale = segments[1];

        // redirect if the path starts with a supported locale
        if (SUPPORTED_LOCALES.includes(maybeLocale)) {
            const newPath = "/" + segments.slice(2).join("/");
            const newUrl = new URL(newPath || "/", origin);

            // 308 = Permanent redirect; preserves query parameters automatically
            return NextResponse.redirect(newUrl, 308);
        }

        return next(request, _next);
    };
};