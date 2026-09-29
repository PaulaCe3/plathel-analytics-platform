import type { components } from "@/types/api.generated";

import { apiRequest } from "./client";

export type ProfileSummary = components["schemas"]["ProfileSummary"];
export type Profile = components["schemas"]["ProfileResponse"];

export function getProfiles(): Promise<ProfileSummary[]> {
  return apiRequest<ProfileSummary[]>("/api/v1/profiles");
}

export function getProfile(profileId: string): Promise<Profile> {
  return apiRequest<Profile>(`/api/v1/profiles/${profileId}`);
}
