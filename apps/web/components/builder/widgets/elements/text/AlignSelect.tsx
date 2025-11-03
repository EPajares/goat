import type { Editor } from "@tiptap/react";

import { ICON_NAME } from "@p4b/ui/components/Icon";

import type { MenuItemOption } from "@/components/builder/widgets/elements/text/MenuSelect";
import { MenuSelect } from "@/components/builder/widgets/elements/text/MenuSelect";

const ALIGN_ITEMS: MenuItemOption[] = [
  { label: "Align Left", value: "left", icon: ICON_NAME.ALIGN_LEFT },
  { label: "Align Center", value: "center", icon: ICON_NAME.ALIGN_CENTER },
  { label: "Align Right", value: "right", icon: ICON_NAME.ALIGN_RIGHT },
  { label: "Justify", value: "justify", icon: ICON_NAME.ALIGN_JUSTIFY },
];

export const AlignSelect = ({ editor }: { editor: Editor | null }) => {
  if (!editor) return null;

  const currentAlign =
    (editor.isActive({ textAlign: "center" }) && "center") ||
    (editor.isActive({ textAlign: "right" }) && "right") ||
    (editor.isActive({ textAlign: "justify" }) && "justify") ||
    "left";

  return (
    <MenuSelect
      buttonValue="textAlign"
      items={ALIGN_ITEMS}
      value={currentAlign}
      onChange={(val) => {
        editor.chain().focus().setTextAlign(val).run();
      }}
    />
  );
};
