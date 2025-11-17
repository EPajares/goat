import type { StoryFn, Meta } from "@storybook/react";

import { createPageStory } from "../login/createPageStory";

const pageId = "login-verify-email.ftl";

const { PageStory } = createPageStory({ pageId });

export default {
  title: "Pages/Auth/Login Verify Email",
  component: PageStory,
} as Meta<typeof PageStory>;

export const Default: StoryFn<typeof PageStory> = () => <PageStory />;
