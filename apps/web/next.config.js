const withBundleAnalyzer = require("@next/bundle-analyzer")({
  enabled: process.env.ANALYZE === "true",
});
const { withSentryConfig } = require("@sentry/nextjs");

const nextConfig = {
  output: "standalone",
  reactStrictMode: true,
  transpilePackages: ["@p4b/ui", "@p4b/tsconfig"],
  modularizeImports: {
    "@mui/icons-material": {
      transform: "@mui/icons-material/{{member}}",
    },
  },
  images: {
    domains: ["assets.plan4better.de", "source.unsplash.com"],
  },
  webpack: (config) => {
    config.module.exprContextCritical = false; // Todo: Added to suppress warnings from cog-protocol (Find a better solution)
    return config;
  },
};

const sentryConfig = {
  // For all available options, see:
  // https://github.com/getsentry/sentry-webpack-plugin#options
  org: "plan4better",
  project: "goat-frontend",
  // Suppresses source map uploading logs during build
  silent: true,
  // Upload a larger set of source maps for prettier stack traces (increases build time)
  widenClientFileUpload: true,
  // Routes browser requests to Sentry through a Next.js rewrite to circumvent ad-blockers (increases server load)
  tunnelRoute: "/api/monitoring",
  // Hides source maps from generated client bundles
  hideSourceMaps: true,
  // Automatically tree-shake Sentry logger statements to reduce bundle size
  disableLogger: true,
};

const finalConfig = process.env.NEXT_PUBLIC_SENTRY_DSN
  ? withSentryConfig(nextConfig, sentryConfig)
  : nextConfig;

module.exports = withBundleAnalyzer(finalConfig);
