/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone', // Enable standalone output for Docker
  async rewrites() {
    return [
      {
        source: '/api/agent/:path*',
        destination: 'http://localhost:9998/:path*', // Proxy to Python backend
      },
    ];
  },
};

module.exports = nextConfig;
