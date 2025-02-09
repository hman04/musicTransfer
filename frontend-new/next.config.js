/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  poweredByHeader: false,
  compress: true,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_BACKEND_URL}/:path*`
      }
    ]
  },
  experimental: {
    optimizeCss: true,
    optimizePackageImports: ['@chakra-ui/react']
  }
}

module.exports = nextConfig 