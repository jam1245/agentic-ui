/**
 * Session-level artifact registry (front-end half).
 *
 * Holds the ArtifactContext for every artifact rendered this session, so the chat agent
 * can stay data-aware. Dependency-free: a tiny observable store consumable via
 * `useSyncExternalStore` (swap for Zustand/Redux if you already use one — the shape and
 * the digest projection are what matter, not the library).
 *
 * NOTE on architecture: in this repo the backend (server/genesis_app.py) is the source of
 * truth for artifacts and the chat reads them from the /api/chat response, so this client
 * store is an optional convenience/reference for client-side UI. For durable, multi-tab, or
 * server-reasoned follow-ups, keep the backend store authoritative (a DB in production).
 * See docs/09-artifact-aware-context.md.
 */
import { useSyncExternalStore } from "react";
import type { ArtifactContext, ArtifactDigest } from "../contract";
import { toDigest } from "../contract";

type Listener = () => void;

class ArtifactRegistry {
  private artifacts = new Map<string, ArtifactContext>();
  private listeners = new Set<Listener>();
  private snapshot: ArtifactContext[] = [];

  upsert(artifact: ArtifactContext) {
    this.artifacts.set(artifact.artifactId, artifact);
    this.emit();
  }

  get(artifactId: string): ArtifactContext | undefined {
    return this.artifacts.get(artifactId);
  }

  /** Full rows for one artifact — the "rehydrate on demand" path (client cache hit). */
  getFullData(artifactId: string): Record<string, unknown>[] | undefined {
    return this.artifacts.get(artifactId)?.fullData;
  }

  /** Compact, prompt-safe digests of all artifacts — feed THESE to the chat agent. */
  digests(): ArtifactDigest[] {
    return this.snapshot.map(toDigest);
  }

  list = (): ArtifactContext[] => this.snapshot;

  clear() {
    this.artifacts.clear();
    this.emit();
  }

  subscribe = (l: Listener): (() => void) => {
    this.listeners.add(l);
    return () => this.listeners.delete(l);
  };

  getSnapshot = (): ArtifactContext[] => this.snapshot;

  private emit() {
    this.snapshot = [...this.artifacts.values()];
    this.listeners.forEach((l) => l());
  }
}

/** One registry per browser session. */
export const artifactRegistry = new ArtifactRegistry();

/** React hook: re-renders when artifacts change. */
export function useArtifacts(): ArtifactContext[] {
  return useSyncExternalStore(artifactRegistry.subscribe, artifactRegistry.getSnapshot, artifactRegistry.getSnapshot);
}

export function useArtifactDigests(): ArtifactDigest[] {
  const artifacts = useArtifacts();
  return artifacts.map(toDigest);
}
