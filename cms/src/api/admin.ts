import { apiRequest } from "./client";
import type { PublishResult, PublishRun, ReferenceData, ValidationReport } from "./types";

export function getValidationReport() {
  return apiRequest<ValidationReport>("/admin/validation-report");
}

export function publishCatalog() {
  return apiRequest<PublishResult>("/admin/catalog/publish", { method: "POST" });
}

export function getPublishRuns() {
  return apiRequest<PublishRun[]>("/admin/catalog/publish-runs");
}

export function getReferenceData() {
  return apiRequest<ReferenceData>("/reference");
}