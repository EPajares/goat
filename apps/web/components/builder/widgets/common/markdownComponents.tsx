import { Box } from "@mui/material";
import type { Components } from "react-markdown";
import React from "react";

import { parseBareVideoParagraph, parseVideoEmbed, type VideoEmbed } from "@/lib/utils/mediaEmbed";

/**
 * A directly-hosted video. Deliberately not an iframe: a media element cannot
 * execute script, so nothing an author types becomes markup or a document.
 *
 * `preload="metadata"` fetches enough for a first frame without pulling the
 * whole file into a popup that may never be played.
 */
const VideoEmbedPlayer = ({ src, poster }: VideoEmbed) => (
  <Box
    component="video"
    controls
    preload="metadata"
    poster={poster}
    src={src}
    sx={{
      display: "block",
      // Fill the width and let the height follow the video's own ratio. A fixed
      // maxHeight here pillarboxes anything wider than that ratio allows — the
      // box keeps the full width while the picture shrinks to fit the cap.
      width: "100%",
      height: "auto",
      // Only a guard against a portrait source turning the popup into a column;
      // it never binds for ordinary landscape video, including 4:3.
      maxHeight: "80vh",
      my: 1,
      borderRadius: 1,
    }}
  />
);

/** Text of a react-markdown child list, when it is plain text only. */
const textOf = (children: React.ReactNode): string | null => {
  const nodes = React.Children.toArray(children);
  if (nodes.length !== 1) return null;
  return typeof nodes[0] === "string" ? nodes[0] : null;
};

/**
 * Shared react-markdown overrides for popup content.
 *
 * Used by both the renderer and the editor's Preview tab so that what an author
 * previews is what a reader gets.
 */
export const popupMarkdownComponents: Components = {
  // A paragraph containing only a video URL becomes the player. `video` is
  // phrasing content, so it is valid inside the <p> react-markdown emits.
  p: ({ children, ...props }) => {
    const text = textOf(children);
    const embed = text ? parseBareVideoParagraph(text) : null;
    if (embed) return <VideoEmbedPlayer {...embed} />;
    return <p {...props}>{children}</p>;
  },

  // ![](clip.mp4 "poster.jpg") — an <img> pointing at a video renders nothing
  // useful, so treat it as an embed.
  img: ({ src, title, alt, ...props }) => {
    const embed = parseVideoEmbed(typeof src === "string" ? src : undefined, title);
    if (embed) return <VideoEmbedPlayer {...embed} />;
    return <img src={src} title={title ?? undefined} alt={alt ?? ""} {...props} />;
  },

  // [label](clip.mp4) — same, and otherwise make links safe to follow.
  a: ({ href, title, children, ...props }) => {
    const embed = parseVideoEmbed(href, title);
    if (embed) return <VideoEmbedPlayer {...embed} />;
    return (
      <a href={href} title={title ?? undefined} target="_blank" rel="noopener noreferrer" {...props}>
        {children}
      </a>
    );
  },
};
