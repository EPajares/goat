import type { StoryFn, Meta } from "@storybook/react";

import { createPageStory } from "../login/createPageStory";

const { PageStory } = createPageStory({
  pageId: "login-idp-link-email.ftl",
});

export default {
  title: "Pages/Auth/Link Idp Email",
  component: PageStory,
} as Meta<typeof PageStory>;

export const Default: StoryFn<typeof PageStory> = () => <PageStory />;
