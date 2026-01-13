import * as z from "zod";

import { invitationStatusEnum } from "@/lib/validations/invitation";

const regionEnum = z.enum(["EU"]);

const organizationBaseSchema = z.object({
  name: z.string().min(1).max(50),
  type: z.string().min(1).max(50),
  size: z.string().min(1).max(50),
  industry: z.string().min(1).max(150),
  department: z.string().min(1).max(150),
  use_case: z.string().min(1).max(250),
  phone_number: z.string().min(1).max(50),
  location: z.string().min(1).max(50),
  avatar: z.string(),
});

const planNameEnum = z.enum(["goat_starter", "goat_professional", "goat_enterprise"]);

export const planNames = {
  STARTER: "goat_starter",
  PRO: "goat_professional",
  ENTERPRISE: "goat_enterprise",
} as const;

export enum FeatureName {
  SCENARIO = "SCENARIO",
}

export const featureToPlanMap = {
  [FeatureName.SCENARIO]: [planNames.PRO, planNames.ENTERPRISE],
};

export const organizationRolesEnum = z.enum([
  "organization-owner",
  "organization-admin",
  "organization-editor",
  "organization-viewer",
]);

export const organizationRoles = {
  OWNER: "organization-owner",
  ADMIN: "organization-admin",
  EDITOR: "organization-editor",
  VIEWER: "organization-viewer",
} as const;

const organizationSchema = organizationBaseSchema.extend({
  id: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
  total_storage: z.number(),
  used_storage: z.number().default(0),
  total_credits: z.number(),
  used_credits: z.number().default(0),
  total_projects: z.number(),
  used_projects: z.number().default(0),
  total_editors: z.number(),
  used_editors: z.number().default(1),
  total_viewers: z.number(),
  used_viewers: z.number().default(0),
  plan_name: planNameEnum,
  plan_renewal_date: z.string(),
  on_trial: z.boolean(),
  region: regionEnum,
  contact_user_id: z.string(),
  hubspot_id: z.string().optional(),
  suspended: z.boolean(),
});

const organizationMemberSchema = z.object({
  id: z.string(),
  firstname: z.string().optional(),
  lastname: z.string().optional(),
  email: z.string(),
  roles: z.array(z.string()),
  invitation_status: invitationStatusEnum,
  avatar: z.string(),
});
export const organizationMemberQueryParams = z.object({
  include_invitations: z.boolean().optional(),
});

export const invitationCreateSchema = z.object({
  user_email: z.string().email(),
  role: organizationRolesEnum,
  expires: z.string().optional(),
});

export const organizationUpdateSchema = organizationBaseSchema.partial();

export const postOrganizationSchema = organizationBaseSchema.extend({
  region: regionEnum,
  newsletter_subscribe: z.boolean(),
});

export type Organization = z.infer<typeof organizationSchema>;
export type OrganizationMember = z.infer<typeof organizationMemberSchema>;
export type OrganizationUpdate = z.infer<typeof organizationUpdateSchema>;
export type InvitationCreate = z.infer<typeof invitationCreateSchema>;
export type PostOrganization = z.infer<typeof postOrganizationSchema>;
export type OrganizationMemberQueryParams = z.infer<typeof organizationMemberQueryParams>;
