import { describe, expect, it } from "vitest";

import {
  isImageUrl,
  isVideoUrl,
  parseBareVideoParagraph,
  parseVideoEmbed,
  stripMediaUrls,
} from "@/lib/utils/mediaEmbed";

/** The real source from the BBSR Stadtklimadashboard page. */
const BBSR_MP4 =
  "https://www.bbsr.bund.de/BBSR/DE/forschung/programme/exwost/jahr/2024/stadtklimadashboard/video/erklaervideo-stadtkilmadashboard.mp4?__blob=videoFile&v=3";
const BBSR_POSTER =
  "https://www.bbsr.bund.de/BBSR/DE/forschung/programme/exwost/jahr/2024/stadtklimadashboard/video/erklaervideo-stadtkilmadashboard-startbild.jpg?__blob=normal&v=2";

describe("isVideoUrl", () => {
  it("accepts a directly hosted video, query string and all", () => {
    expect(isVideoUrl(BBSR_MP4)).toBe(true);
    expect(isVideoUrl("https://host/clip.webm")).toBe(true);
    expect(isVideoUrl("https://host/clip.MP4")).toBe(true);
  });

  it("rejects http — it would be blocked as mixed content and play nothing", () => {
    expect(isVideoUrl("http://host/clip.mp4")).toBe(false);
  });

  it("rejects anything that is not a video file", () => {
    expect(isVideoUrl("https://host/page.html")).toBe(false);
    expect(isVideoUrl("https://www.youtube.com/watch?v=abc")).toBe(false);
    expect(isVideoUrl("https://host/photo.jpg")).toBe(false);
    expect(isVideoUrl("https://host/")).toBe(false);
  });

  it("rejects scheme tricks rather than treating them as sources", () => {
    expect(isVideoUrl("javascript:alert(1)//clip.mp4")).toBe(false);
    expect(isVideoUrl("data:video/mp4;base64,AAAA")).toBe(false);
    expect(isVideoUrl("//host/clip.mp4")).toBe(false);
    expect(isVideoUrl("not a url .mp4")).toBe(false);
    expect(isVideoUrl("")).toBe(false);
  });

  it("is not fooled by a video extension in the query only", () => {
    expect(isVideoUrl("https://host/page?file=clip.mp4")).toBe(false);
  });
});

describe("isImageUrl", () => {
  it("accepts https images, and nothing else", () => {
    expect(isImageUrl(BBSR_POSTER)).toBe(true);
    expect(isImageUrl("https://host/poster.png")).toBe(true);
    expect(isImageUrl("http://host/poster.png")).toBe(false);
    expect(isImageUrl("https://host/clip.mp4")).toBe(false);
  });
});

describe("parseVideoEmbed", () => {
  it("reads the source of a video link", () => {
    expect(parseVideoEmbed(BBSR_MP4)).toEqual({ src: BBSR_MP4 });
  });

  it("takes a poster from the markdown title", () => {
    expect(parseVideoEmbed(BBSR_MP4, BBSR_POSTER)).toEqual({ src: BBSR_MP4, poster: BBSR_POSTER });
  });

  it("ignores a title that is not an image, keeping the video", () => {
    expect(parseVideoEmbed(BBSR_MP4, "Erklärvideo")).toEqual({ src: BBSR_MP4 });
    expect(parseVideoEmbed(BBSR_MP4, "http://host/poster.jpg")).toEqual({ src: BBSR_MP4 });
  });

  it("returns null for a normal link, so it renders as a link", () => {
    expect(parseVideoEmbed("https://example.com/page")).toBeNull();
    expect(parseVideoEmbed(undefined)).toBeNull();
  });

  it("trims surrounding whitespace", () => {
    expect(parseVideoEmbed(` ${BBSR_MP4} `)).toEqual({ src: BBSR_MP4 });
  });
});

describe("parseBareVideoParagraph", () => {
  it("embeds a paragraph that is only a video URL", () => {
    expect(parseBareVideoParagraph(BBSR_MP4)).toEqual({ src: BBSR_MP4 });
    expect(parseBareVideoParagraph(`\n  ${BBSR_MP4}\n`)).toEqual({ src: BBSR_MP4 });
  });

  it("leaves prose alone, even when it mentions a video", () => {
    expect(parseBareVideoParagraph(`Sehen Sie ${BBSR_MP4}`)).toBeNull();
    expect(parseBareVideoParagraph("Hier finden Sie unser Erklärvideo:")).toBeNull();
    expect(parseBareVideoParagraph("")).toBeNull();
  });
});

describe("stripMediaUrls", () => {
  it("drops a standalone video URL from text-only renderings", () => {
    // Tooltips render plain text; a raw URL there is noise.
    expect(stripMediaUrls(`Erklärvideo: ${BBSR_MP4}`)).toBe("Erklärvideo:");
    expect(stripMediaUrls(BBSR_MP4)).toBe("");
  });

  it("keeps ordinary text and non-video links", () => {
    expect(stripMediaUrls("Ein Satz über das Dashboard")).toBe("Ein Satz über das Dashboard");
    expect(stripMediaUrls("Mehr: https://example.com/page")).toBe("Mehr: https://example.com/page");
  });

  it("collapses the whitespace it leaves behind", () => {
    expect(stripMediaUrls(`vor ${BBSR_MP4} nach`)).toBe("vor nach");
  });
});
