/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  reactStrictMode: true,
  poweredByHeader: false,
  // This repo has no ESLint config; `next build` must not depend on ESLint
  // being installed (the CI job is a build, not a lint — see .github/workflows/ci.yml).
  eslint: { ignoreDuringBuilds: true },
};

export default nextConfig;
