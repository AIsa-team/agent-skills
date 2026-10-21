export const PLATFORMS = ["amazon-us", "tiktok-shop-us", "shopify"] as const;
export type Platform = (typeof PLATFORMS)[number];
export const SUPPORTED_PLATFORMS = PLATFORMS;
export const PLATFORM_SUPPORT = {
  supported: [
    { platform: "amazon-us", markets: ["US"], scope: "Product detail page main/gallery images, listing copy, product video" },
    { platform: "tiktok-shop-us", markets: ["US"], scope: "Shop product gallery, listing copy, product listing video" },
    { platform: "shopify", markets: "User-specified market", scope: "Store product media and copy; theme-specific requirements must be researched" },
  ],
  video: "Experimental Wan adapter; explicit playbook opt-in and a matching public HTTPS photo required. No live generation verified in this release.",
  planned: ["etsy-us", "ebay-us", "amazon-uk", "amazon-de", "amazon-jp", "tiktok-shop-uk", "shopee-sg", "shopee-my", "lazada-sg", "lazada-my", "aliexpress-us", "aliexpress-eu"],
  roadmap: {
    "next (planned)": ["etsy-us", "ebay-us"],
    "following (planned)": ["amazon-uk", "amazon-de", "amazon-jp", "tiktok-shop-uk"],
    "later (planned)": ["shopee-sg", "shopee-my", "lazada-sg", "lazada-my", "aliexpress-us", "aliexpress-eu"],
  },
} as const;
export type MediaKind = "image" | "copy" | "video";
export const PLACEMENTS = {
  "amazon-main": { platform: "amazon-us", kind: "image" },
  "amazon-gallery": { platform: "amazon-us", kind: "image" },
  "amazon-copy": { platform: "amazon-us", kind: "copy" },
  "amazon-video": { platform: "amazon-us", kind: "video" },
  "tiktok-gallery": { platform: "tiktok-shop-us", kind: "image" },
  "tiktok-copy": { platform: "tiktok-shop-us", kind: "copy" },
  "tiktok-video": { platform: "tiktok-shop-us", kind: "video" },
  "shopify-gallery": { platform: "shopify", kind: "image" },
  "shopify-copy": { platform: "shopify", kind: "copy" },
  "shopify-video": { platform: "shopify", kind: "video" },
} as const satisfies Record<string, { platform: Platform; kind: MediaKind }>;
export type Placement = keyof typeof PLACEMENTS;

export interface ReferenceInput {
  id: string;
  sku: string;
  path: string;
  source: "user-product-photo";
  remoteUrl?: string;
}
export interface ValidatedReference extends ReferenceInput {
  sha256: string;
  mimeType: "image/png" | "image/jpeg" | "image/webp";
  width: number;
  height: number;
}
export interface ProductFact {
  id: string;
  text: string;
  source: {
    kind: "user-confirmed" | "visible-in-reference" | "document";
    note?: string;
    referenceId?: string;
    url?: string;
  };
}
export interface Product {
  sku: string;
  name: string;
  category: string;
  facts: ProductFact[];
}
export interface PlatformTarget {
  platform: Platform;
  market: string;
  language: string;
  placements: Placement[];
  themeUrl?: string;
  themeDescription?: string;
}
export interface Brief {
  name: string;
  goal: string;
  targets: PlatformTarget[];
  products: Product[];
  references: ReferenceInput[];
  budget: {
    currency: "USD";
    maxEstimatedCostUsd: number;
    maxAttemptsPerDeliverable: number;
  };
}
export interface ResearchRule {
  id: string;
  platform: Platform;
  placement: Placement;
  requirement: string;
  status: "mandatory" | "recommended";
  sourceUrl: string;
  publisher: string;
  fetchedAt: string;
  effectiveAt: string | null;
  conflict: string | null;
}
export interface ResearchExample {
  id: string;
  platform: Platform;
  placement: Placement;
  url: string;
  observedAt: string;
  metricTier: "measured" | "platform-selected" | "proxy";
  metrics: { name: string; value: number | string | null; window: string | null }[];
  takeaways: string[];
}
export interface Research {
  scope: string;
  rules: ResearchRule[];
  examples: ResearchExample[];
  exampleLimitations?: { platform: Platform; reason: string }[];
  synthesis: string[];
  limitations: string[];
}
export interface Deliverable {
  id: string;
  sku: string;
  platform: Platform;
  placement: Placement;
  kind: MediaKind;
  referenceIds: string[];
  claimIds: string[];
  ruleIds: string[];
  prompt: string;
  model: string;
  imageMode?: "preserve" | "edit";
  imageSize?: "1K" | "2K" | "4K";
  allowExperimentalVideo?: boolean;
  size?: string;
  durationSeconds?: number;
  copyLimits?: Record<string, number>;
  constraints?: {
    minWidth?: number;
    minHeight?: number;
    maxBytes?: number;
    maxDurationSeconds?: number;
    aspectRatio?: string;
  };
  estimatedCostUsd: number;
  pricingSource?: string;
  pricingCheckedAt?: string;
  successCriteria: string[];
}
export interface Playbook {
  title: string;
  version: string;
  summary: string;
  creativeDirection: string;
  deliverables: Deliverable[];
  budget: {
    estimatedTotalUsd: number;
    maxAttemptsPerDeliverable: number;
    costControl: "estimate-only";
  };
  approvalNotes: string[];
}
export interface Approval {
  actor: "user";
  message: string;
  playbookHash: string;
  approvedAt: string;
}
export interface ProjectState {
  schemaVersion: 1;
  brief: Brief;
  references: ValidatedReference[];
  research?: Research;
  playbook?: Playbook;
  approval?: Approval;
  createdAt: string;
  updatedAt: string;
}
