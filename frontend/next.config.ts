import type { NextConfig } from "next";
import { config } from "dotenv";
import { resolve } from "path";

// Load environment variables from parent directory
config({ path: resolve(__dirname, "../.env") });
config({ path: resolve(__dirname, "../.env.development.local") });

const nextConfig: NextConfig = {
  /* config options here */
};

export default nextConfig;
