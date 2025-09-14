/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    // Always use local backend via Cloudflare tunnel for demo
    NEXT_PUBLIC_HOST: 'https://local.faqbuddy.net',
  },
};

export default nextConfig;
