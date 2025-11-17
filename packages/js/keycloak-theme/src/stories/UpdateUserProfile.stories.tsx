import type { StoryFn, Meta } from "@storybook/react";

import { createPageStory } from "../login/createPageStory";

const pageId = "update-user-profile.ftl";

const { PageStory } = createPageStory({ pageId });

export default {
  title: "Pages/Auth/Update User Profile",
  component: PageStory,
} as Meta<typeof PageStory>;

export const Default: StoryFn<typeof PageStory> = () => <PageStory />;
