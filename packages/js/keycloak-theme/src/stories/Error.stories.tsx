import type { StoryFn, Meta } from "@storybook/react";

import { createPageStory } from "../login/createPageStory";

const pageId = "error.ftl";

const { PageStory } = createPageStory({ pageId });

export default {
  title: "Pages/Auth/Error",
  component: PageStory,
} as Meta<typeof PageStory>;

export const Default: StoryFn<typeof PageStory> = () => <PageStory />;

export const WithAnotherMessage: StoryFn<typeof PageStory> = () => (
  <PageStory
    kcContext={{
      message: { summary: "With another error message" },
    }}
  />
);

