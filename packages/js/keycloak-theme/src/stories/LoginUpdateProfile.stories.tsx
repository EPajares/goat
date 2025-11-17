import type { StoryFn, Meta } from "@storybook/react";

import { createPageStory } from "../login/createPageStory";

const pageId = "login-update-profile.ftl";

const { PageStory } = createPageStory({ pageId });

export default {
  title: "Pages/Auth/Login Update Profile",
  component: PageStory,
} as Meta<typeof PageStory>;

export const Default: StoryFn<typeof PageStory> = () => <PageStory />;
