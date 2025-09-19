import { Box, Divider, Paper, Stack, styled } from "@mui/material";
import { debounce } from "@mui/material/utils";
import Subscript from "@tiptap/extension-subscript";
import Superscript from "@tiptap/extension-superscript";
import TextAlign from "@tiptap/extension-text-align";
import type { Editor } from "@tiptap/react";
import { EditorContent, useEditor, useEditorState } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { useEffect, useState } from "react";

import { ICON_NAME } from "@p4b/ui/components/Icon";

import type { TextElementSchema } from "@/lib/validations/widget";

import { ArrowPopper } from "@/components/ArrowPoper";
import { AlignSelect } from "@/components/builder/widgets/elements/text/AlignSelect";
import { BlockTypeSelect } from "@/components/builder/widgets/elements/text/BlockTypeSelect";
import MenuButton from "@/components/builder/widgets/elements/text/MenuButton";

const extensions = [
  StarterKit,
  Subscript,
  Superscript,
  TextAlign.configure({
    types: ["heading", "paragraph"],
  }),
];

export const TipTapEditorContent = styled(EditorContent)(({ theme }) => ({
  flexGrow: 1,
  height: "100%",
  padding: theme.spacing(1),
  overflowY: "auto",
  "& > .ProseMirror-focused": {
    outline: `1px solid ${theme.palette.primary.main}`,
    borderRadius: theme.shape.borderRadius,
  },
  "& > .ProseMirror:focus": {
    outline: `1px solid ${theme.palette.primary.main}`,
    borderRadius: theme.shape.borderRadius,
  },
}));

const ToolbarContainer = styled(Paper)(({ theme }) => ({
  display: "flex",
  alignItems: "center",
  padding: theme.spacing(2),
  borderRadius: theme.shape.borderRadius * 2,
  boxShadow: theme.shadows[4],
  backgroundColor: theme.palette.background.paper,
}));

const TextElementWidgetViewOnly = ({ config }: { config: TextElementSchema }) => {
  const editor = useEditor({
    extensions,
    content: config.setup.text || "",
    immediatelyRender: true,
    shouldRerenderOnTransaction: false,
    editable: false,
  });

  return <TipTapEditorContent editor={editor} />;
};

const TextElementWidgetEditable = ({
  config,
  onWidgetUpdate,
}: {
  config: TextElementSchema;
  onWidgetUpdate?: (newConfig: TextElementSchema) => void;
}) => {
  const editor = useEditor({
    extensions,
    content: config.setup.text || "",
    immediatelyRender: true,
    shouldRerenderOnTransaction: false,
    editable: true,
  });

  const [toolbarOpen, setToolbarOpen] = useState(false);

  useEffect(() => {
    if (!editor) return;

    const handleFocus = () => setToolbarOpen(true);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const handleBlur = ({ event }: any) => {
      if (event?.relatedTarget && (event.relatedTarget as HTMLElement).closest(".tiptap-toolbar")) return;
      setToolbarOpen(false);
    };

    editor.on("focus", handleFocus);
    editor.on("blur", handleBlur);

    return () => {
      editor.off("focus", handleFocus);
      editor.off("blur", handleBlur);
    };
  }, [editor]);

  const editorState = useEditorState({
    editor,
    selector: ({ editor }: { editor: Editor }) => ({
      isBold: editor.isActive("bold"),
      isItalic: editor.isActive("italic"),
      isUnderline: editor.isActive("underline"),
      isStrike: editor.isActive("strike"),
      isSuperscript: editor.isActive("superscript"),
      isSubscript: editor.isActive("subscript"),
      isLink: editor.isActive("link"),
    }),
  });

  const debouncedUpdate = debounce(() => {
    if (editor && onWidgetUpdate) {
      onWidgetUpdate({
        ...config,
        setup: { ...config.setup, text: editor.getHTML() },
      });
    }
  }, 300); // Adjust debounce delay as needed

  useEffect(() => {
    if (!editor) return;

    const handleUpdate = () => {
      debouncedUpdate();
    };

    editor.on("update", handleUpdate);

    return () => {
      editor.off("update", handleUpdate);
    };
  }, [editor, debouncedUpdate]);

  return (
    <Box>
      <TipTapEditorContent editor={editor} />

      <ArrowPopper
        open={toolbarOpen}
        disablePortal={false}
        placement="bottom"
        isClickAwayEnabled
        content={
          <ToolbarContainer className="tiptap-toolbar">
            {editor && (
              <Stack direction="row" spacing={1} alignItems="center">
                <BlockTypeSelect editor={editor} />
                {/* <ListTypeSelect editor={editor} /> */}
                <Divider flexItem orientation="vertical" />
                <Stack direction="row" spacing={0.5} alignItems="center">
                  <MenuButton
                    value="bold"
                    iconName={ICON_NAME.BOLD}
                    selected={editorState?.isBold}
                    onClick={() => editor.chain().focus().toggleBold().run()}
                  />
                  <MenuButton
                    value="italic"
                    iconName={ICON_NAME.ITALIC}
                    selected={editorState?.isItalic}
                    onClick={() => editor.chain().focus().toggleItalic().run()}
                  />
                  <MenuButton
                    value="underline"
                    iconName={ICON_NAME.UNDERLINE}
                    selected={editorState?.isUnderline}
                    onClick={() => editor.chain().focus().toggleUnderline().run()}
                  />
                  <MenuButton
                    value="strike"
                    iconName={ICON_NAME.STRIKETHROUGH}
                    selected={editorState?.isStrike}
                    onClick={() => editor.chain().focus().toggleStrike().run()}
                  />
                  <MenuButton
                    value="superscript"
                    iconName={ICON_NAME.SUPERSCRIPT}
                    selected={editorState?.isSuperscript}
                    onClick={() => editor.chain().focus().toggleSuperscript().run()}
                    disabled={!editor.can().toggleSuperscript()}
                  />
                  <MenuButton
                    value="subscript"
                    iconName={ICON_NAME.SUBSCRIPT}
                    selected={editorState?.isSubscript}
                    onClick={() => editor.chain().focus().toggleSubscript().run()}
                    disabled={!editor.can().toggleSubscript()}
                  />
                </Stack>
                <Divider flexItem orientation="vertical" />
                <AlignSelect editor={editor} />
                {/* <Divider flexItem orientation="vertical" />
                <Stack direction="row" spacing={0.5} alignItems="center">
                  <MenuButton
                    value="link"
                    iconName={ICON_NAME.LINK}
                    selected={editorState?.isLink}
                    // onClick={() => editor.chain().focus().toggleLink().run()}
                    disabled={!editor.can().toggleLink()}
                  />
                </Stack> */}
              </Stack>
            )}
          </ToolbarContainer>
        }>
        <Box />
      </ArrowPopper>
    </Box>
  );
};

const TextElementWidget = ({
  config,
  viewOnly = false,
  onWidgetUpdate,
}: {
  config: TextElementSchema;
  viewOnly?: boolean;
  onWidgetUpdate?: (newConfig: TextElementSchema) => void;
}) => {
  return viewOnly ? (
    <TextElementWidgetViewOnly config={config} />
  ) : (
    <TextElementWidgetEditable config={config} onWidgetUpdate={onWidgetUpdate} />
  );
};

export default TextElementWidget;
