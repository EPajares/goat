import type { StoryFn, Meta } from "@storybook/react";

import { createPageStory } from "../login/createPageStory";

const { PageStory } = createPageStory({
  pageId: "login-page-expired.ftl",
});

export default {
  title: "Pages/Auth/Login Page Expired",
  component: PageStory,
} as Meta<typeof PageStory>;

export const Default: StoryFn<typeof PageStory> = () => <PageStory />;
