import type { NextConfig } from "next";
import path from "node:path";

const nextConfig: NextConfig = {
  // Static export → plain HTML/CSS/JS in out/, hostable free anywhere.
  output: "export",
  images: { unoptimized: true },

  // Pin the Turbopack workspace root to this folder. The repo root is a Python
  // project, so Next would otherwise mis-infer the root and crash on recompile.
  turbopack: { root: path.resolve(__dirname) },

  // For GitHub Pages under a project path, set basePath: "/docapi".
};

export default nextConfig;
