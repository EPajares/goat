import type { StoryFn, Meta } from "@storybook/react";

import { createPageStory } from "../login/createPageStory";

const { PageStory } = createPageStory({
  pageId: "login-config-totp.ftl",
});

export default {
  title: "Pages/Auth/Configure TOTP",
  component: PageStory,
} as Meta<typeof PageStory>;

export const Default: StoryFn<typeof PageStory> = () => <PageStory />;

export const WithManualSetUp: StoryFn<typeof PageStory> = () => (
  <PageStory
    kcContext={{
      mode: "manual",
    }}
  />
);

export const WithError: StoryFn<typeof PageStory> = () => (
  <PageStory
    kcContext={{
      messagesPerField: {
        get: (fieldName: string) =>
          fieldName === "totp" ? "Invalid TOTP" : undefined,
        exists: (fieldName: string) => fieldName === "totp",
        existsError: (fieldName: string) => fieldName === "totp",
        printIfExists: <T,>(fieldName: string, x: T) =>
          fieldName === "totp" ? x : undefined,
      },
    }}
  />
);
