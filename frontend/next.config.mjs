/** @type {import('next').NextConfig} */

// Check if we should use local development
const USE_LOCAL = process.env.NEXT_PUBLIC_USE_LOCAL === 'true';

const nextConfig = {
  env: {
    // Only override HOST if USE_LOCAL is true, otherwise use default (remote)
    ...(USE_LOCAL && {
      NEXT_PUBLIC_HOST: 'http://localhost:8000'
    })
  }
};

// Log the configuration
if (USE_LOCAL) {
  console.log('INFO: Frontend configured for LOCAL development');
  console.log('WHERE: API Host: http://localhost:8000');
} else {
  console.log('INFO: Frontend configured for REMOTE/PRODUCTION');
}

export default nextConfig;
