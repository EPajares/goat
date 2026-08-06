type IdentifiedFeature = { id?: string | number };

/**
 * Append a freshly fetched page onto an accumulated list, skipping features that
 * are already there.
 *
 * Infinite-scroll callers hold the page cursor and the fetched payload as
 * separate state, so a render can land where the cursor has already advanced but
 * the payload is still the previous page — appending it would duplicate every
 * row of that page. Features without an id are always appended, since there is
 * nothing to compare them by.
 */
export const appendUniqueFeatures = <T extends IdentifiedFeature>(previous: T[], incoming: T[]): T[] => {
  const seen = new Set(previous.map((feature) => feature.id).filter((id) => id !== undefined));
  const fresh = incoming.filter((feature) => feature.id === undefined || !seen.has(feature.id));
  return fresh.length ? [...previous, ...fresh] : previous;
};
