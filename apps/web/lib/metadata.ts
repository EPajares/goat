import { isValidUrl } from "@/lib/utils/helpers";
import type { Metadata } from "next";


type LanguageMetadataContent = {
  title: string;
  description: string;
  locale: string;
  image: string;
};

type OtherOptions = {
  openGraphUrl?: string;
  robotsIndex?: boolean;
};

type PartialLanguageMetadataContent = Partial<LanguageMetadataContent>;

const defaultContentMap: Record<string, LanguageMetadataContent> = {
  en: {
    title: "GOAT | WebGIS with Planning Intelligence",
    description: "Intelligent software for modern web mapping and integrated planning",
    locale: "en_US",
    image: "https://assets.plan4better.de/img/thumbnails/goat/social_media_preview_en.png",
  },
  de: {
    title: "GOAT | WebGIS mit Planungsintelligenz",
    description: "Intelligente Software für modernes Web-Mapping und integrierte Planung",
    locale: "de_DE",
    image: "https://assets.plan4better.de/img/thumbnails/goat/social_media_preview_de.png",
  },
};

export function getLocalizedMetadata(
  lng: string,
  partialContentMap: Record<string, PartialLanguageMetadataContent> = {},
  otherOptions: OtherOptions = {}
): Metadata {
  const defaultContent = defaultContentMap[lng] || defaultContentMap["en"];
  const overrides = partialContentMap[lng] || {};

  const content: LanguageMetadataContent = {
    title: overrides.title ?? defaultContent.title,
    description: overrides.description ?? defaultContent.description,
    locale: overrides.locale ?? defaultContent.locale,
    image: overrides.image ?? defaultContent.image,
  };

  const openGraphUrl = otherOptions.openGraphUrl || process.env.NEXT_PUBLIC_APP_URL

  let robotsIndex = otherOptions.robotsIndex !== undefined ? !!otherOptions.robotsIndex : false;

  if (openGraphUrl && (openGraphUrl.includes("localhost") || openGraphUrl.includes("dev") || openGraphUrl.includes("staging"))) {
    // Disable indexing for local development or staging environments
    robotsIndex = false;
  }


  return {
    metadataBase: openGraphUrl && isValidUrl(openGraphUrl) ? new URL(openGraphUrl) : undefined,
    title: content.title,
    description: content.description,
    openGraph: {
      url: openGraphUrl,
      title: content.title,
      description: content.description,
      locale: content.locale,
      siteName: "GOAT",
      type: "website",
      images: [
        {
          url: content.image,
          secureUrl: content.image,
          width: 1200,
          height: 630,
          alt: content.title,
          type: "image/png",
        },
      ],
    },
    twitter: {
      title: content.title,
      description: content.description,
      card: "summary_large_image",
      images: [content.image],
      creator: "@plan4better",
      site: "@plan4better",
    },
    robots: {
      index: robotsIndex,
    },
  };
}
