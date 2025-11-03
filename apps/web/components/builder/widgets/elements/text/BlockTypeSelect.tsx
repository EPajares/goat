import type { Editor } from "@tiptap/react";
import { useEditorState } from "@tiptap/react";

import { ICON_NAME } from "@p4b/ui/components/Icon";

import type { MenuItemOption } from "@/components/builder/widgets/elements/text/MenuSelect";
import { MenuSelect } from "@/components/builder/widgets/elements/text/MenuSelect";

const BLOCK_TYPE_ITEMS: MenuItemOption[] = [
  { label: "Text", value: "paragraph", icon: ICON_NAME.TEXT },
  { label: "Heading 1", value: "heading1", icon: ICON_NAME.H1 },
  { label: "Heading 2", value: "heading2", icon: ICON_NAME.H2 },
  { label: "Heading 3", value: "heading3", icon: ICON_NAME.H3 },
  { label: "Bulleted list", value: "bulletList", icon: ICON_NAME.BULLET_LIST },
  { label: "Numbered list", value: "orderedList", icon: ICON_NAME.NUMBERED_LIST },
  { label: "Code block", value: "codeBlock", icon: ICON_NAME.CODE },
];

const getCurrentBlock = (editor: Editor) => {
  if (editor.isActive("bulletList")) return "bulletList";
  if (editor.isActive("orderedList")) return "orderedList";
  if (editor.isActive("codeBlock")) return "codeBlock";
  if (editor.isActive("paragraph")) return "paragraph";
  if (editor.isActive("heading", { level: 1 })) return "heading1";
  if (editor.isActive("heading", { level: 2 })) return "heading2";
  if (editor.isActive("heading", { level: 3 })) return "heading3";
  return "paragraph";
};

export const BlockTypeSelect = ({ editor }: { editor: Editor | null }) => {
  const editorState = useEditorState({
    editor,
    selector: (snapshot) => {
      const e = snapshot.editor;
      return { currentBlock: e ? getCurrentBlock(e) : "paragraph" };
    },
  });

  if (!editor) return null;

  return (
    <MenuSelect
      buttonValue="blockType"
      items={BLOCK_TYPE_ITEMS}
      value={editorState?.currentBlock ?? "paragraph"}
      onChange={(val) => {
        switch (val) {
          case "bulletList":
            editor.chain().focus().toggleBulletList().run();
            break;
          case "orderedList":
            editor.chain().focus().toggleOrderedList().run();
            break;
          case "codeBlock":
            editor.chain().focus().toggleCodeBlock().run();
            break;
          case "paragraph":
            editor.chain().focus().setParagraph().run();
            break;
          case "heading1":
            editor.chain().focus().toggleHeading({ level: 1 }).run();
            break;
          case "heading2":
            editor.chain().focus().toggleHeading({ level: 2 }).run();
            break;
          case "heading3":
            editor.chain().focus().toggleHeading({ level: 3 }).run();
            break;
        }
      }}
    />
  );
};
