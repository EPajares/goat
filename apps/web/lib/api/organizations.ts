import useSWR from "swr";

import { apiRequestAuth, fetcher } from "@/lib/api/fetcher";
import type {
  InvitationCreate,
  Organization,
  OrganizationMember,
  OrganizationMemberQueryParams,
  OrganizationUpdate,
  PostOrganization,
} from "@/lib/validations/organization";

export const ORG_API_BASE_URL = new URL("api/v1/organizations", process.env.NEXT_PUBLIC_ACCOUNTS_API_URL)
  .href;

export const useOrganizationMembers = (organizationId: string, queryParams?: OrganizationMemberQueryParams) => {
  const { data, isLoading, error, mutate, isValidating } = useSWR<OrganizationMember[]>(
    () => (organizationId ? [`${ORG_API_BASE_URL}/${organizationId}/users`, queryParams] : null),

    fetcher
  );
  return {
    members: data,
    isLoading: isLoading,
    isError: error,
    mutate,
    isValidating,
  };
};


export const createOrganization = async (payload: PostOrganization): Promise<Organization> => {
  const response = await apiRequestAuth(`${ORG_API_BASE_URL}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error("Failed to create folder");
  }
  return await response.json();
};

export const updateOrganization = async (organization_id: string, organization: OrganizationUpdate) => {
  const response = await apiRequestAuth(`${ORG_API_BASE_URL}/${organization_id}/profile`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(organization),
  });
  if (!response.ok) throw await response.json();
  return response;
};

export const deleteOrganization = async (organization_id: string) => {
  const response = await apiRequestAuth(`${ORG_API_BASE_URL}/${organization_id}`, {
    method: "DELETE",
  });
  if (!response.ok) throw await response.json();
  return response;
};

export const deleteMember = async (organization_id: string, user_id: string) => {
  const response = await apiRequestAuth(`${ORG_API_BASE_URL}/${organization_id}/users/${user_id}`, {
    method: "DELETE",
  });
  if (!response.ok) throw await response.json();
  return response;
};

export const updateOrganizationMemberRole = async (
  organization_id: string,
  user_id: string,
  role: string
) => {
  const response = await apiRequestAuth(`${ORG_API_BASE_URL}/${organization_id}/users/${user_id}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ role }),
  });
  if (!response.ok) throw await response.json();
  return response;
}


export const updateOrganizationInvitationRole = async (
  organization_id: string,
  invitation_id: string,
  role: string
) => {
  const response = await apiRequestAuth(
    `${ORG_API_BASE_URL}/${organization_id}/invitations/${invitation_id}/role`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ role }),
    }
  );
  if (!response.ok) throw await response.json();
  return response;
}

export const deleteInvitation = async (organization_id: string, invitation_id: string) => {
  const response = await apiRequestAuth(
    `${ORG_API_BASE_URL}/${organization_id}/invitations/${invitation_id}`,
    {
      method: "DELETE",
    }
  );
  if (!response.ok) throw await response.json();
  return response;
};

export const updateMember = async (organization_id: string, user_id: string, role: string) => {
  const response = await apiRequestAuth(`${ORG_API_BASE_URL}/${organization_id}/users/${user_id}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ role }),
  });
  if (!response.ok) throw await response.json();
  return response;
};

export const transferOwnership = async (organization_id: string, user_id: string) => {
  const response = await apiRequestAuth(
    `${ORG_API_BASE_URL}/${organization_id}/users/${user_id}/transfer-ownership`,
    {
      method: "PATCH",
    }
  );
  if (!response.ok) throw await response.json();
  return response;
};

export const inviteMember = async (organization_id: string, invitation: InvitationCreate) => {
  const response = await apiRequestAuth(`${ORG_API_BASE_URL}/${organization_id}/invitations`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(invitation),
  });
  if (!response.ok) throw await response.json();
  return response;
};
