import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.API_BASE_URL || "http://localhost:8010"}/:path*`,
      },
    ];
  },
  // Increase server-side fetch timeout for the LLM pipeline (default 30s is too short)
  serverExternalPackages: [],
  experimental: {
    proxyTimeout: 120_000,
  },
};

export default nextConfig;
