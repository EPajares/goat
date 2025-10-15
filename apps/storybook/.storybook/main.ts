import type { StorybookConfig } from "@storybook/nextjs";

const config: StorybookConfig = {
  core: {
    disableTelemetry: true,
  },
  stories: [
    "../../../packages/js/keycloak-theme/src/stories/*.mdx",
    "../../../packages/js/keycloak-theme/src/stories/*.stories.@(js|jsx|ts|tsx)",
    "../../../packages/js/ui/stories/**/*.mdx",
    "../../../packages/js/ui/stories/**/*.stories.@(js|jsx|ts|tsx)",
  ],
  addons: [
    "@storybook/addon-links",
    "@storybook/addon-essentials",
    "@storybook/addon-interactions",
    "@storybook/addon-a11y",
    "storybook-dark-mode",
    "@storybook/addon-designs",
  ],
  docs: {
    autodocs: "tag",
  },
  framework: {
    name: "@storybook/nextjs",
    options: {},
  },
  staticDirs: ["../public", "../../../packages/js/keycloak-theme/public"],
};
export default config;
