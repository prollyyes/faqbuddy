/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    // For demo - points to your local backend via Cloudflare tunnel
    NEXT_PUBLIC_HOST: process.env.NODE_ENV === 'development' 
      ? 'https://rag.faqbuddy.net'  // Your local backend via tunnel
      : 'https://faqbuddy-hs0j.onrender.com', // Production backend
  },
};

export default nextConfig;
