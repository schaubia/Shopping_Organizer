/** @type {import('next').NextConfig} */
const nextConfig = {
  // Images from USDA or user uploads
  images: { domains: ["fdc.nal.usda.gov"] },
  // Proxy API calls to FastAPI in dev — avoids CORS issues
  async rewrites() {
    return [
      {
        source:      "/api/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
