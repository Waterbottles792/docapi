import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Static export → plain HTML/CSS/JS in out/, hostable free anywhere.
  output: "export",
  images: { unoptimized: true },

  // For GitHub Pages under a project path, set basePath: "/docapi".
};

export default nextConfig;
