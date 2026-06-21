/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  async rewrites() {
    return [
      {
        source: "/backend/:path*",
        destination: "http://34.172.68.235:8000/:path*",
      },
    ];
  },
};

export default nextConfig;