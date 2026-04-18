/** @type {import('next').NextConfig} */
const nextConfig = {
  allowedDevOrigins: ['10.1.129.232'],
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  output: "standalone",
  eslint: {
    ignoreDuringBuilds: true,
  },
}

export default nextConfig
