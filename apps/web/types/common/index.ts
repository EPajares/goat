export type NestedPartial<T> = {
  [P in keyof T]?: NestedPartial<T[P]>;
};

export enum ContentActions {
  INFO = "info",
  EDIT_METADATA = "editMetadata",
  MOVE_TO_FOLDER = "moveToFolder",
  DOWNLOAD = "download",
  SHARE = "share",
  DELETE = "delete",
  TABLE = "table",
  UPDATE = "update",
}

export enum MapLayerActions {
  CHART = "chart",
  DUPLICATE = "duplicate",
  RENAME = "rename",
  ZOOM_TO = "zoomTo",
  PROPERTIES = "properties",
  STYLE = "style",
}

export enum ScenarioActions {
  EDIT = "edit",
  EDIT_METADATA = "editMetadata",
  DELETE = "delete",
}

export enum LayerStyleActions {
  RESET = "reset",
  SAVE_AS_DEFAULT = "saveAsDefault",
}

export enum FilterExpressionActions {
  DELETE = "delete",
  DUPLICATE = "duplicate",
}

export enum OrgMemberActions {
  EDIT = "edit",
  DELETE = "delete",
  TRANSFER_OWNERSHIP = "transferOwnership",
  CANCEL_INVITATION = "cancelInvitation",
}

export enum TeamMemberActions {
  DELETE = "delete",
  CANCEL_INVITATION = "cancelInvitation",
}

export type ResponseResult = {
  message: string;
  status?: "error" | "success";
};

export enum AddLayerSourceType {
  DatasourceExplorer,
  DatasourceUpload,
  DataSourceExternal,
  CatalogExplorer,
}
