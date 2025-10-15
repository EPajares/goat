import type { StoryFn, Meta } from "@storybook/react";

import { createPageStory } from "../login/createPageStory";

const { PageStory } = createPageStory({
  pageId: "login.ftl",
});

export default {
  title: "Pages/Auth/Login",
  component: PageStory,
} as Meta<typeof PageStory>;

export const Default: StoryFn<typeof PageStory> = () => <PageStory />;

export const WithoutPasswordField: StoryFn<typeof PageStory> = () => (
  <PageStory
    kcContext={{
      realm: { password: false },
    }}
  />
);

export const WithoutRegistration: StoryFn<typeof PageStory> = () => (
  <PageStory
    kcContext={{
      realm: { registrationAllowed: false },
    }}
  />
);

export const WithoutRememberMe: StoryFn<typeof PageStory> = () => (
  <PageStory
    kcContext={{
      realm: { rememberMe: false },
    }}
  />
);

export const WithoutPasswordReset: StoryFn<typeof PageStory> = () => (
  <PageStory
    kcContext={{
      realm: { resetPasswordAllowed: false },
    }}
  />
);

export const WithEmailAsUsername: StoryFn<typeof PageStory> = () => (
  <PageStory
    kcContext={{
      realm: { loginWithEmailAllowed: false },
    }}
  />
);

export const WithPresetUsername: StoryFn<typeof PageStory> = () => (
  <PageStory
    kcContext={{
      login: { username: "info@plan4better.de" },
    }}
  />
);

export const WithImmutablePresetUsername: StoryFn<typeof PageStory> = () => (
  <PageStory
    kcContext={{
      auth: {
        attemptedUsername: "info@plan4better.de",
        showUsername: true,
      },
      message: { type: "info", summary: "Please re-authenticate to continue" },
    }}
  />
);

export const WithSocialProviders: StoryFn<typeof PageStory> = () => (
  <PageStory
    kcContext={{
      social: {
        displayInfo: true,
        providers: [
          {
            loginUrl: "google",
            alias: "google",
            providerId: "google",
            displayName: "Google",
          },
          {
            loginUrl: "microsoft",
            alias: "microsoft",
            providerId: "microsoft",
            displayName: "Microsoft",
          },
          {
            loginUrl: "facebook",
            alias: "facebook",
            providerId: "facebook",
            displayName: "Facebook",
          },
          {
            loginUrl: "instagram",
            alias: "instagram",
            providerId: "instagram",
            displayName: "Instagram",
          },
          {
            loginUrl: "twitter",
            alias: "twitter",
            providerId: "twitter",
            displayName: "Twitter",
          },
          {
            loginUrl: "linkedin",
            alias: "linkedin",
            providerId: "linkedin",
            displayName: "LinkedIn",
          },
          {
            loginUrl: "stackoverflow",
            alias: "stackoverflow",
            providerId: "stackoverflow",
            displayName: "Stackoverflow",
          },
          {
            loginUrl: "github",
            alias: "github",
            providerId: "github",
            displayName: "Github",
          },
          {
            loginUrl: "gitlab",
            alias: "gitlab",
            providerId: "gitlab",
            displayName: "Gitlab",
          },
          {
            loginUrl: "bitbucket",
            alias: "bitbucket",
            providerId: "bitbucket",
            displayName: "Bitbucket",
          },
          {
            loginUrl: "paypal",
            alias: "paypal",
            providerId: "paypal",
            displayName: "PayPal",
          },
          {
            loginUrl: "openshift",
            alias: "openshift",
            providerId: "openshift",
            displayName: "OpenShift",
          },
        ],
      },
    }}
  />
);
