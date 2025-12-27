import useSWR from "swr";

import { apiRequestAuth, fetcher } from "@/lib/api/fetcher";
import type { Team, TeamBase, TeamMember, TeamUpdate } from "@/lib/validations/team";

const ACCOUNTS_BASE = process.env.NEXT_PUBLIC_ACCOUNTS_API_URL;
export const ACCOUNTS_ENABLED = Boolean(ACCOUNTS_BASE);

export const TEAMS_API_BASE_URL = ACCOUNTS_ENABLED ? new URL("api/v1/teams", ACCOUNTS_BASE!).href : "";

const ACCOUNTS_DISABLED_ERROR = { error: "ACCOUNTS_DISABLED" } as const;

// Stubs for OSS mode
const STUB_TEAMS: Team[] = [];
const STUB_TEAM: Team = { id: "local-team", name: "Local Team" } as unknown as Team;
const STUB_TEAM_MEMBERS: TeamMember[] = [];

// Hooks

export const useTeams = () => {
  const disabled = !ACCOUNTS_ENABLED;
  const { data, isLoading, error, mutate, isValidating } = useSWR<Team[]>(
    disabled ? null : `${TEAMS_API_BASE_URL}`,
    fetcher,
    {
      fallbackData: STUB_TEAMS,
      revalidateOnFocus: !disabled,
      revalidateOnReconnect: !disabled,
      shouldRetryOnError: !disabled,
    }
  );
  return {
    teams: data ?? STUB_TEAMS,
    isLoading,
    isError: error,
    mutate,
    isValidating,
  };
};

export const useTeam = (teamId: string) => {
  const disabled = !ACCOUNTS_ENABLED || !teamId;
  const { data, isLoading, error, mutate, isValidating } = useSWR<Team>(
    disabled ? null : `${TEAMS_API_BASE_URL}/${teamId}`,
    fetcher,
    {
      fallbackData: STUB_TEAM,
      revalidateOnFocus: !disabled,
      revalidateOnReconnect: !disabled,
      shouldRetryOnError: !disabled,
    }
  );
  return {
    team: data ?? STUB_TEAM,
    isLoading,
    isError: error,
    mutate,
    isValidating,
  };
};

export const useTeamMembers = (teamId: string) => {
  const disabled = !ACCOUNTS_ENABLED || !teamId;
  const { data, isLoading, error, mutate, isValidating } = useSWR<TeamMember[]>(
    disabled ? null : `${TEAMS_API_BASE_URL}/${teamId}/members`,
    fetcher,
    {
      fallbackData: STUB_TEAM_MEMBERS,
      revalidateOnFocus: !disabled,
      revalidateOnReconnect: !disabled,
      shouldRetryOnError: !disabled,
    }
  );
  return {
    teamMembers: data ?? STUB_TEAM_MEMBERS,
    isLoading,
    isError: error,
    mutate,
    isValidating,
  };
};

// Mutations

export const createTeam = async (payload: TeamBase) => {
  if (!ACCOUNTS_ENABLED) throw ACCOUNTS_DISABLED_ERROR;
  const response = await apiRequestAuth(`${TEAMS_API_BASE_URL}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    try {
      throw await response.json();
    } catch {
      throw new Error("Failed to create team");
    }
  }
  return await response.json();
};

export const updateTeam = async (teamId: string, organization: TeamUpdate) => {
  if (!ACCOUNTS_ENABLED) throw ACCOUNTS_DISABLED_ERROR;
  const response = await apiRequestAuth(`${TEAMS_API_BASE_URL}/${teamId}/profile`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(organization),
  });
  if (!response.ok) throw await response.json();
  return response;
};

export const deleteTeam = async (teamId: string) => {
  if (!ACCOUNTS_ENABLED) throw ACCOUNTS_DISABLED_ERROR;
  const response = await apiRequestAuth(`${TEAMS_API_BASE_URL}/${teamId}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    try {
      throw await response.json();
    } catch {
      throw new Error("Failed to delete team");
    }
  }
  return await response.json();
};

export const deleteMember = async (teamId: string, memberId: string) => {
  if (!ACCOUNTS_ENABLED) throw ACCOUNTS_DISABLED_ERROR;
  const response = await apiRequestAuth(`${TEAMS_API_BASE_URL}/${teamId}/users/${memberId}`, {
    method: "DELETE",
  });
  if (!response.ok) throw await response.json();
  return response;
};

export const createTeamMember = async (teamId: string, memberId: string) => {
  if (!ACCOUNTS_ENABLED) throw ACCOUNTS_DISABLED_ERROR;
  const response = await apiRequestAuth(`${TEAMS_API_BASE_URL}/${teamId}/users/${memberId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!response.ok) {
    try {
      throw await response.json();
    } catch {
      throw new Error("Failed to add team member");
    }
  }
  return await response.json();
};
