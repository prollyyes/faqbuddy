/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    NEXT_PUBLIC_HOST: 'http://localhost:8000' // for local testing
    // NEXT_PUBLIC_HOST: 'https://api.faqbuddy.net'
  }
};

export default nextConfig;
