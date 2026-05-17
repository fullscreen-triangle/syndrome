/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        // Map /tools/:tool  →  static HTML at public/tools/:tool/index.html
        // :tool matches a single path segment, so /tools/core/spectral.js is NOT matched
        source: '/tools/:tool',
        destination: '/tools/:tool/index.html',
      },
    ];
  },
}

module.exports = nextConfig
