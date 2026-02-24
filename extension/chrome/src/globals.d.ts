declare function successResponse(payload?: Record<string, unknown>): Record<string, unknown>;
declare function errorResponse(message?: string, extra?: Record<string, unknown>): Record<string, unknown>;
declare function getSelectedClipData(): { title: string; url: string; raw_content: string };
declare function registerContentMessageHandlers(): void;
declare function mapChromeRuntimeErrorToMessage(lastError?: unknown, fallback?: string): string;
declare function getApiBaseUrl(): string;
declare function getClipsEndpoint(): string;
declare function createClip(clip: Record<string, unknown>): Promise<unknown>;
declare function registerContextMenuHandlers(): void;
declare function registerMessageHandlers(): void;

interface Error {
  status?: number;
  body?: string;
}
