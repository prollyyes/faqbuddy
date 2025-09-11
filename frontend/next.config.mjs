/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    NEXT_PUBLIC_HOST: process.env.NODE_ENV === 'production' 
      ? 'https://api.faqbuddy.net' 
      : 'http://localhost:8000'
  }
};

export default nextConfig;
