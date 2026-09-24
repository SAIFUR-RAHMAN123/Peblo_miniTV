import { useState } from "react";

/**
 * Shows a neutral placeholder block until the image finishes loading (or
 * falls back to it permanently if there's no url / it fails), so slow or
 * missing artwork never leaves a blank hole in a row or hero.
 */
export function LazyImage({
  src,
  alt,
  className,
}: {
  src: string | null | undefined;
  alt: string;
  className?: string;
}) {
  const [loaded, setLoaded] = useState(false);
  const [failed, setFailed] = useState(false);

  if (!src || failed) {
    return <div className={`lazy-image lazy-image-placeholder ${className ?? ""}`} aria-label={alt} />;
  }

  return (
    <div className={`lazy-image ${className ?? ""}`}>
      {!loaded && <div className="lazy-image-placeholder" />}
      <img
        src={src}
        alt={alt}
        loading="lazy"
        onLoad={() => setLoaded(true)}
        onError={() => setFailed(true)}
        style={{ opacity: loaded ? 1 : 0 }}
      />
    </div>
  );
}