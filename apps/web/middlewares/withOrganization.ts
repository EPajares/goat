import { getToken } from "next-auth/jwt";
import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

import type { InvitationPaginated } from "@/lib/validations/invitation";

import { refreshAccessToken } from "@/app/api/auth/[...nextauth]/options";
import type { MiddlewareFactory } from "@/middlewares/types";

const protectedPaths = ["/home", "/projects", "/datasets", "/settings", "/map"];
const publicPaths = ["/map/public"];

export const withOrganization: MiddlewareFactory = (next) => {
  return async (request: NextRequest, _next) => {
    if (
      process.env.NEXT_PUBLIC_AUTH_DISABLED ||
      process.env.NEXT_PUBLIC_ACCOUNTS_DISABLED ||
      !process.env.NEXTAUTH_URL ||
      !process.env.NEXTAUTH_SECRET ||
      !process.env.NEXT_PUBLIC_ACCOUNTS_API_URL
    ) {
      return next(request, _next);
    }

    const USERS_API_BASE_URL = new URL("api/v1/users", process.env.NEXT_PUBLIC_ACCOUNTS_API_URL).href;

    const { pathname, origin, basePath } = request.nextUrl;

    // Skip public paths
    const isPublicPath = publicPaths.some((p) => pathname.startsWith(p));
    if (isPublicPath) return next(request, _next);

    // Skip unprotected paths
    const isProtected = protectedPaths.some((p) => pathname.startsWith(p));
    if (!isProtected) return next(request, _next);

    const token = await getToken({
      req: request,
      secret: process.env.NEXTAUTH_SECRET,
    });
    if (!token) return next(request, _next);

    try {
      let _token = token;

      // Refresh expired token
      if (Date.now() >= token.expires_at * 1000) {
        _token = await refreshAccessToken(token);
      }

      // Check user's organization status
      const orgRes = await fetch(`${USERS_API_BASE_URL}/organization`, {
        headers: {
          Authorization: `Bearer ${_token.access_token}`,
        },
      });

      if (orgRes.ok) {
        const organization = await orgRes.json();

        // Suspended org
        if (organization?.suspended) {
          return NextResponse.redirect(new URL(`${basePath}/onboarding/organization/suspended`, origin));
        }

        // Valid org
        if (organization?.id) {
          const response = (await next(request, _next)) as NextResponse;
          response.cookies.set("organization", organization.id, { path: "/" });
          return response;
        }
      }

      // Check for invitations
      const invitationRes = await fetch(
        `${USERS_API_BASE_URL}/invitations?type=organization&status=pending`,
        {
          headers: {
            Authorization: `Bearer ${_token.access_token}`,
          },
        }
      );

      if (invitationRes.ok) {
        const invitations: InvitationPaginated = await invitationRes.json();
        if (invitations?.items?.length > 0) {
          const firstInvitationId = invitations.items[0].id;
          return NextResponse.redirect(
            new URL(`${basePath}/onboarding/organization/invite/${firstInvitationId}`, origin)
          );
        }
      }
    } catch (error) {
      console.error("Error while fetching organization", error);
    }

    // No org or invite → redirect to create org page
    const createUrl = new URL(`${basePath}/onboarding/organization/create`, origin);
    return NextResponse.redirect(createUrl);
  };
};
