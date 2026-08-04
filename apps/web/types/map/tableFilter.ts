import type { Expression } from "@/lib/validations/filter";

/**
 * What a table host gives the column filter popover so it can read and change
 * filters without knowing where they live.
 *
 * The map data table backs this with the project layer's CQL (persisted, and
 * shared with the layer Filter panel). A public dashboard table will back it
 * with view state ANDed onto the author's base filter, so a viewer's filter is
 * never written into the published config.
 */
export type TableFilterController = {
  /** Current expressions, parsed from whatever the host stores. */
  expressions: Expression[];
  /** How the host combines them. The popover shows a warning when it is "or". */
  logicalOperator: "and" | "or";
  /** Replace the expression with this id, or append when the id is unknown. */
  upsert: (expression: Expression) => Promise<void> | void;
  remove: (id: string) => Promise<void> | void;
  /** False for viewers who may not change this host's filters. */
  canEdit: boolean;
};
