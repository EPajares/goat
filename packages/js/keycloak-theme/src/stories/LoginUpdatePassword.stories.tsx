import type { StoryFn, Meta } from "@storybook/react";

import { createPageStory } from "../login/createPageStory";

const pageId = "login-update-password.ftl";

const { PageStory } = createPageStory({ pageId });

export default {
  title: "Pages/Auth/Login Update Password",
  component: PageStory,
} as Meta<typeof PageStory>;

export const Default: StoryFn<typeof PageStory> = () => <PageStory />;

export const AppInitiatedAction: StoryFn<typeof PageStory> = () => (
  <PageStory
    kcContext={{
      isAppInitiatedAction: true,
    }}
  />
);
