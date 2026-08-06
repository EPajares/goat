import { render } from "@testing-library/react";
import ReactMarkdown from "react-markdown";
import { describe, expect, it } from "vitest";

import { popupMarkdownComponents } from "@/components/builder/widgets/common/markdownComponents";

const BBSR_MP4 =
  "https://www.bbsr.bund.de/BBSR/DE/forschung/programme/exwost/jahr/2024/stadtklimadashboard/video/erklaervideo-stadtkilmadashboard.mp4?__blob=videoFile&v=3";
const BBSR_POSTER =
  "https://www.bbsr.bund.de/BBSR/DE/forschung/programme/exwost/jahr/2024/stadtklimadashboard/video/erklaervideo-stadtkilmadashboard-startbild.jpg?__blob=normal&v=2";

const renderMarkdown = (markdown: string) =>
  render(<ReactMarkdown components={popupMarkdownComponents}>{markdown}</ReactMarkdown>);

describe("popup markdown components", () => {
  it("turns a bare video URL on its own line into a player", () => {
    const { container } = renderMarkdown(`Hier finden Sie unser Erklärvideo:\n\n${BBSR_MP4}`);

    const video = container.querySelector("video");
    expect(video).not.toBeNull();
    expect(video?.getAttribute("src")).toBe(BBSR_MP4);
    expect(video?.hasAttribute("controls")).toBe(true);
    // The whole file should not download just because a popup opened.
    expect(video?.getAttribute("preload")).toBe("metadata");
    // The surrounding prose still renders.
    expect(container.textContent).toContain("Erklärvideo");
  });

  it("does not cap the height in pixels, which would pillarbox the video", () => {
    // A fixed maxHeight with width:100% leaves the box wider than the video's
    // ratio allows, so the picture shrinks and the sides render as bars.
    const { container } = renderMarkdown(BBSR_MP4);
    const style = getComputedStyle(container.querySelector("video")!);
    expect(style.height).toBe("auto");
    expect(style.maxHeight).not.toMatch(/^\d+px$/);
  });

  it("keeps the player out of an invalid <p> wrapper", () => {
    const { container } = renderMarkdown(BBSR_MP4);
    // <video> is phrasing content so a <p> would be legal, but a paragraph that
    // is only a video should not add one — no stray empty paragraphs either.
    expect(container.querySelectorAll("p")).toHaveLength(0);
    expect(container.querySelector("video")).not.toBeNull();
  });

  it("reads a poster from the markdown title", () => {
    const { container } = renderMarkdown(`![](${BBSR_MP4} "${BBSR_POSTER}")`);
    const video = container.querySelector("video");
    expect(video?.getAttribute("poster")).toBe(BBSR_POSTER);
  });

  it("takes a poster on link syntax too", () => {
    const { container } = renderMarkdown(`[Erklärvideo](${BBSR_MP4} "${BBSR_POSTER}")`);
    expect(container.querySelector("video")?.getAttribute("poster")).toBe(BBSR_POSTER);
  });

  it("plays without a poster rather than breaking when none is given", () => {
    const { container } = renderMarkdown(BBSR_MP4);
    const video = container.querySelector("video");
    expect(video).not.toBeNull();
    expect(video?.hasAttribute("poster")).toBe(false);
  });

  it("ignores a caption-style title, keeping the video playable", () => {
    // Authors will write a human title here; it must not become a poster URL.
    const { container } = renderMarkdown(`![](${BBSR_MP4} "Erklärvideo Stadtklimadashboard")`);
    const video = container.querySelector("video");
    expect(video?.getAttribute("src")).toBe(BBSR_MP4);
    expect(video?.hasAttribute("poster")).toBe(false);
  });

  it("embeds a video written with image or link syntax", () => {
    expect(renderMarkdown(`![Erklärvideo](${BBSR_MP4})`).container.querySelector("video")).not.toBeNull();
    expect(renderMarkdown(`[Erklärvideo](${BBSR_MP4})`).container.querySelector("video")).not.toBeNull();
  });

  it("leaves ordinary images and links alone", () => {
    const image = renderMarkdown('![Karte](https://host/map.png "Eine Karte")').container;
    expect(image.querySelector("video")).toBeNull();
    expect(image.querySelector("img")?.getAttribute("src")).toBe("https://host/map.png");
    expect(image.querySelector("img")?.getAttribute("alt")).toBe("Karte");

    const link = renderMarkdown("[BBSR](https://www.bbsr.bund.de/)").container;
    expect(link.querySelector("video")).toBeNull();
    const anchor = link.querySelector("a");
    expect(anchor?.getAttribute("href")).toBe("https://www.bbsr.bund.de/");
    // External links must not hand the opener over.
    expect(anchor?.getAttribute("rel")).toContain("noopener");
    expect(anchor?.getAttribute("target")).toBe("_blank");
  });

  it("does not build a player from an http or non-video URL", () => {
    expect(renderMarkdown("http://host/clip.mp4").container.querySelector("video")).toBeNull();
    expect(
      renderMarkdown("https://www.youtube.com/watch?v=abc").container.querySelector("video")
    ).toBeNull();
  });

  it("renders a URL inside a sentence as text, not a player", () => {
    const { container } = renderMarkdown(`Das Video ${BBSR_MP4} erklärt alles.`);
    expect(container.querySelector("video")).toBeNull();
    expect(container.querySelector("p")).not.toBeNull();
  });

  it("still renders the markdown it always did", () => {
    const { container } = renderMarkdown("# Titel\n\n**fett** und *kursiv*\n\n- eins\n- zwei");
    expect(container.querySelector("h1")?.textContent).toBe("Titel");
    expect(container.querySelector("strong")?.textContent).toBe("fett");
    expect(container.querySelector("em")?.textContent).toBe("kursiv");
    expect(container.querySelectorAll("li")).toHaveLength(2);
  });
});
