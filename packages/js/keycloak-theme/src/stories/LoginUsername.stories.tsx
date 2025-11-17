import type { StoryFn, Meta } from "@storybook/react";

import { createPageStory } from "../login/createPageStory";

const pageId = "login-username.ftl";

const { PageStory } = createPageStory({ pageId });

export default {
  title: "Pages/Auth/Login Username",
  component: PageStory,
} as Meta<typeof PageStory>;

export const Default: StoryFn<typeof PageStory> = () => <PageStory />;
