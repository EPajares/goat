import { fetcher, apiRequestAuth } from "@/lib/api/fetcher";
import type { Team, TeamBase, TeamMember, TeamUpdate } from "@/lib/validations/team";
import useSWR from "swr";

export const TEAMS_API_BASE_URL = new URL(
  "api/v1/teams",
  process.env.NEXT_PUBLIC_ACCOUNTS_API_URL
).href;


export const useTeams = () => {
  const { data, isLoading, error, mutate, isValidating } = useSWR<Team[]>(
    () => [`${TEAMS_API_BASE_URL}`],

    fetcher
  );
  return {
    teams: data,
    isLoading: isLoading,
    isError: error,
    mutate,
    isValidating,
  };
};

export const useTeam = (teamId: string) => {
  const { data, isLoading, error, mutate, isValidating } = useSWR<Team>(
    () => [`${TEAMS_API_BASE_URL}/${teamId}`],
    fetcher
  );
  return {
    team: data,
    isLoading: isLoading,
    isError: error,
    mutate,
    isValidating,
  };
}

export const useTeamMembers = (teamId: string) => {
  const { data, isLoading, error, mutate, isValidating } = useSWR<TeamMember[]>(
    () => [`${TEAMS_API_BASE_URL}/${teamId}/members`],
    fetcher
  );
  return {
    teamMembers: data,
    isLoading: isLoading,
    isError: error,
    mutate,
    isValidating,
  };
}


export const createTeam = async (payload: TeamBase) => {
  const response = await apiRequestAuth(`${TEAMS_API_BASE_URL}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error("Failed to create team");
  }
  return await response.json();
}

export const updateTeam = async (teamId: string, organization: TeamUpdate) => {
  const response = await apiRequestAuth(`${TEAMS_API_BASE_URL}/${teamId}/profile`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(organization),
  });
  if (!response.ok) throw await response.json();
  return response;
};


export const deleteTeam = async (teamId: string) => {
  const response = await apiRequestAuth(`${TEAMS_API_BASE_URL}/${teamId}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error("Failed to delete team");
  }
  return await response.json();
}

export const deleteMember = async (teamId: string, memberId: string) => {
  const response = await apiRequestAuth(`${TEAMS_API_BASE_URL}/${teamId}/users/${memberId}`, {
    method: "DELETE",
  });
  if (!response.ok) throw await response.json();
  return response;
};


export const createTeamMember = async (teamId: string, memberId: string) => {
  const response = await apiRequestAuth(`${TEAMS_API_BASE_URL}/${teamId}/users/${memberId}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
  });
  return await response.json();
}
