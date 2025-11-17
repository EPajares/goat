import useSWR from "swr";

import { apiRequestAuth, fetcher } from "@/lib/api/fetcher";
import type { InvitationPaginated } from "@/lib/validations/invitation";
import type { Organization } from "@/lib/validations/organization";
import type { GetInvitationsQueryParams, User, UserUpdate } from "@/lib/validations/user";

// Toggle by presence of NEXT_PUBLIC_ACCOUNTS_API_URL
const ACCOUNTS_BASE = process.env.NEXT_PUBLIC_ACCOUNTS_API_URL;
export const ACCOUNTS_ENABLED = Boolean(ACCOUNTS_BASE);

export const USERS_API_BASE_URL = ACCOUNTS_ENABLED ? new URL("api/v1/users", ACCOUNTS_BASE!).href : "";

// Stubs for OSS mode
const nowIso = new Date().toISOString();

const STUB_USER: User = {
  id: "local-user",
  email: "local@plan4better.de",
  avatar: "",
  firstname: "Local",
  lastname: "User",
  newsletter_subscribe: false,
  roles: [],
  organization_id: "local-org",
  created_at: nowIso,
  updated_at: nowIso,
  enabled: true,
  topt: false,
};

const STUB_ORGANIZATION: Organization = {
  id: "local-org",
  name: "Local Organization",
  type: "OSS",
  size: "1",
  industry: "OSS",
  department: "Core",
  use_case: "Local usage",
  phone_number: "",
  location: "Local",
  avatar: "",
  created_at: nowIso,
  updated_at: nowIso,
  total_storage: 0,
  used_storage: 0,
  total_credits: 0,
  used_credits: 0,
  total_projects: 0,
  used_projects: 0,
  total_editors: 1,
  used_editors: 1,
  total_viewers: 0,
  used_viewers: 0,
  plan_name: "goat_starter",
  plan_renewal_date: nowIso,
  on_trial: false,
  region: "EU",
  contact_user_id: "local-user",
  hubspot_id: "",
  suspended: false,
};

const STUB_INVITATIONS: InvitationPaginated = {
  items: [],
  total: 0,
  page: 0,
  size: 0,
  pages: 0,
};

const ACCOUNTS_DISABLED_ERROR = { error: "ACCOUNTS_DISABLED" } as const;

// Hooks

export const useOrganization = () => {
  const disabled = !ACCOUNTS_ENABLED;
  const { data, isLoading, error, mutate, isValidating } = useSWR<Organization>(
    disabled ? null : `${USERS_API_BASE_URL}/organization`,
    fetcher,
    {
      fallbackData: STUB_ORGANIZATION,
      revalidateOnFocus: !disabled,
      revalidateOnReconnect: !disabled,
      shouldRetryOnError: !disabled,
    }
  );
  return {
    organization: data!,
    isLoading,
    isError: error,
    mutate,
    isValidating,
  };
};

export const useUserProfile = () => {
  const disabled = !ACCOUNTS_ENABLED;
  const { data, isLoading, error, mutate, isValidating } = useSWR<User>(
    disabled ? null : `${USERS_API_BASE_URL}/profile`,
    fetcher,
    {
      fallbackData: STUB_USER,
      revalidateOnFocus: !disabled,
      revalidateOnReconnect: !disabled,
      shouldRetryOnError: !disabled,
    }
  );
  return {
    userProfile: data!,
    isLoading,
    isError: error,
    mutate,
    isValidating,
  };
};

export const useInvitations = (queryParams?: GetInvitationsQueryParams) => {
  const disabled = !ACCOUNTS_ENABLED;
  const { data, isLoading, error, mutate, isValidating } = useSWR<InvitationPaginated>(
    disabled ? null : [`${USERS_API_BASE_URL}/invitations`, queryParams],
    fetcher,
    {
      fallbackData: STUB_INVITATIONS,
      revalidateOnFocus: !disabled,
      revalidateOnReconnect: !disabled,
      shouldRetryOnError: !disabled,
    }
  );
  return {
    invitations: data!,
    isLoading,
    isError: error,
    mutate,
    isValidating,
  };
};

// Mutations

export const updateUserProfile = async (user: UserUpdate) => {
  if (!ACCOUNTS_ENABLED) throw ACCOUNTS_DISABLED_ERROR;
  const response = await apiRequestAuth(`${USERS_API_BASE_URL}/profile`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(user),
  });
  if (!response.ok) throw await response.json();
  return response;
};

export const acceptInvitation = async (invitationId: string) => {
  if (!ACCOUNTS_ENABLED) throw ACCOUNTS_DISABLED_ERROR;
  const response = await apiRequestAuth(`${USERS_API_BASE_URL}/invitations/${invitationId}`, {
    method: "PATCH",
  });
  if (!response.ok) throw await response.json();
  return response;
};

export const declineInvitation = async (invitationId: string) => {
  if (!ACCOUNTS_ENABLED) throw ACCOUNTS_DISABLED_ERROR;
  const response = await apiRequestAuth(`${USERS_API_BASE_URL}/invitations/${invitationId}`, {
    method: "DELETE",
  });
  if (!response.ok) throw await response.json();
  return response;
};

export const deleteAccount = async () => {
  if (!ACCOUNTS_ENABLED) throw ACCOUNTS_DISABLED_ERROR;
  const response = await apiRequestAuth(`${USERS_API_BASE_URL}`, { method: "DELETE" });
  if (!response.ok) throw await response.json();
  return response;
};
