"use client";

import { FloatingPathsBackground } from "@/components/ui/floating-paths";

/**
 * Site-wide animated background. Sits fixed behind all page content (see
 * `.site-bg` in landing.css). Two path layers, mirrored, for depth.
 * Decorative only — pointer-events disabled so it never intercepts clicks.
 */
export default function SiteBackground() {
  return (
    <div className="site-bg" aria-hidden="true">
      <FloatingPathsBackground position={1} className="absolute inset-0">
        {null}
      </FloatingPathsBackground>
      <FloatingPathsBackground position={-1} className="absolute inset-0">
        {null}
      </FloatingPathsBackground>
    </div>
  );
}
