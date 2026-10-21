export const PLATFORMS = ["amazon-us", "tiktok-shop-us", "shopify"];
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
};
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
};
