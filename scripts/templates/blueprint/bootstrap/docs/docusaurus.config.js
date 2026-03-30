// @ts-check

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: "STACKIT Platform Blueprint",
  tagline: "Reusable local+STACKIT platform blueprint",
  url: "https://example.invalid",
  baseUrl: "/",
  onBrokenLinks: "throw",
  markdown: {
    mermaid: true,
    hooks: {
      onBrokenMarkdownLinks: "throw"
    }
  },
  organizationName: "stackit-platform",
  projectName: "stackit-platform-blueprint",
  i18n: {
    defaultLocale: "en",
    locales: ["en"]
  },
  presets: [
    [
      "classic",
      {
        docs: {
          path: ".",
          routeBasePath: "/",
          sidebarPath: require.resolve("./sidebars.js"),
          editUrl: "https://github.com/stackit-platform/stackit-platform-blueprint/edit/main/docs/",
          include: [
            "README.md",
            "blueprint/**/*.md",
            "platform/**/*.md",
            "reference/generated/**/*.md"
          ]
        },
        blog: false,
        pages: false,
        theme: {
          customCss: require.resolve("./src/css/custom.css")
        }
      }
    ]
  ],
  plugins: [],
  themes: ["@docusaurus/theme-mermaid"],
  themeConfig: {
    navbar: {
      title: "STACKIT Blueprint",
      items: [
        {
          type: "docSidebar",
          sidebarId: "blueprintSidebar",
          position: "left",
          label: "Blueprint"
        },
        {
          type: "docSidebar",
          sidebarId: "platformSidebar",
          position: "left",
          label: "Platform"
        },
        {
          type: "docSidebar",
          sidebarId: "referenceSidebar",
          position: "left",
          label: "Reference"
        }
      ]
    }
  }
};

module.exports = config;
