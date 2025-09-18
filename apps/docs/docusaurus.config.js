// @ts-nocheck
// Note: type annotations allow type checking and IDEs autocompletion

const lightCodeTheme = require("prism-react-renderer/themes/github");
// const darkCodeTheme = require('prism-react-renderer/themes/dracula');
// const DarkTheme = require('@site/src/custom_theme.ts');

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: "GOAT DOCS",
  tagline: "GOATs are cool",
  favicon: "img/favicon.ico",
  url: "https://goat.plan4better.de",
  baseUrl: "/docs/",
  organizationName: "plan4better",
  projectName: "goat",
  onBrokenLinks: "warn",
  onBrokenMarkdownLinks: "warn",
  i18n: {
    defaultLocale: "en",
    locales: ["en", "de"],
    path: "i18n",
    localeConfigs: {
      en: {
        label: "English",
      },
      de: {
        label: "Deutsch",
      },
    },
  },
  presets: [
    [
      "classic",
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          routeBasePath: "/",
          sidebarPath: require.resolve("./sidebars.js"),
          editUrl: ({ locale, versionDocsDirPath, docPath }) => {
            const translation = locale || 'en';
            if (translation !== 'en') {
              return `https://github.com/plan4better/goat/edit/main/apps/docs/i18n/${translation}/docusaurus-plugin-content-docs/current/${docPath}`;
            }
            return `https://github.com/plan4better/goat/edit/main/apps/docs/${docPath}`;
          },
          lastVersion: "current",
          versions: {
            current: {
              label: "2.0",
              path: "2.0",
            },
          },
        },
        theme: {
          customCss: require.resolve("./src/css/custom.css"),
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      // Replace with your project's social card
      image: "img/GOAT_logo_white_green_crop_b.png",
      navbar: {
        logo: {
          alt: "Plan4Better",
          src: "https://assets.plan4better.de/img/logo/plan4better_standard.svg",
        },
        items: [
          {
            type: "docSidebar",
            sidebarId: "tutorialSidebar",
            position: "left",
            label: "Docs",
          },
          {
            to: "https://plan4better.de/en/blog/",
            label: "Blog",
            position: "left",
          },
          {
            type: "localeDropdown",
            position: "right"
          },
          {
            type: "docsVersionDropdown",
            position: "right",
            dropdownActiveClassDisabled: true,
          },
          {
            href: "https://github.com/plan4better/goat",
            label: "GitHub",
            position: "right",
          },
        ],
      },
      footer: {
        links: [
          {
            title: "Community",
            items: [
              {
                label: "LinkedIn",
                href: "https://www.linkedin.com/company/plan4better/",
              },
              {
                label: "GitHub",
                href: "https://github.com/plan4better",
              },
            ],
          },
          {
            title: "More",
            items: [
              {
                label: "Plan4Better",
                to: "https://plan4better.de/en/",
              },
              {
                label: "Blog",
                to: "https://plan4better.de/en/blog/",
              },
              {
                label: "References",
                href: "https://plan4better.de/en/references/",
              },
            ],
          },
        ],
        copyright: `Plan4Better GmbH ${new Date().getFullYear()} | All Rights Reserved`,
      },
      algolia: {
        indexName: 'goat-plan4better',
        appId: 'LLUCN6LJ7S',
        apiKey: '638cac0d311f215315b3313f679af50a',
        contextualSearch: true,
      },
    }),
};

module.exports = config;
