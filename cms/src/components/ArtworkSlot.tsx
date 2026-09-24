import { useRef, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { uploadArtwork } from "../api/episodes";
import { ApiError } from "../api/client";
import type { ArtworkItem, ArtworkSpec } from "../api/types";

export function ArtworkSlot({
  episodePk,
  kind,
  label,
  spec,
  existing,
}: {
  episodePk: number;
  kind: "poster" | "banner" | "thumbnail";
  label: string;
  spec: ArtworkSpec | undefined;
  existing: ArtworkItem | undefined;
}) {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [localPreview, setLocalPreview] = useState<string | null>(null);
  const [errors, setErrors] = useState<string[]>([]);

  const mutation = useMutation({
    mutationFn: (file: File) => uploadArtwork(episodePk, kind, file),
    onSuccess: () => {
      setErrors([]);
      queryClient.invalidateQueries({ queryKey: ["artwork", episodePk] });
    },
    onError: (e: unknown) => {
      if (e instanceof ApiError) setErrors(e.messages);
      else setErrors(["Upload failed. Please try again."]);
    },
  });

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setLocalPreview(URL.createObjectURL(file));
    mutation.mutate(file);
  }

  const previewUrl = localPreview ?? existing?.url;
  const [targetW, targetH] = spec?.target_px ?? [0, 0];

  return (
    <div className="artwork-slot">
      <div className="artwork-slot-header">
        <strong>{label}</strong>
        <span className="artwork-spec-hint">
          {spec ? `${spec.aspect} · ~${targetW}×${targetH}px · max ${spec.max_kb}KB` : ""}
        </span>
      </div>

      <div className={`artwork-preview artwork-preview-${kind}`}>
        {previewUrl ? (
          <img src={previewUrl} alt={`${label} preview`} />
        ) : (
          <div className="artwork-preview-empty">No image uploaded</div>
        )}
      </div>

      {existing && (
        <div className="artwork-meta">
          {existing.width}×{existing.height}px · {(existing.size_bytes / 1024).toFixed(1)}KB
        </div>
      )}

      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/png"
        onChange={handleFileChange}
        disabled={mutation.isPending}
      />
      {mutation.isPending && <div className="artwork-uploading">Uploading...</div>}

      {errors.length > 0 && (
        <ul className="artwork-errors">
          {errors.map((err, i) => (
            <li key={i}>{err}</li>
          ))}
        </ul>
      )}
    </div>
  );
}