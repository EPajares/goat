import { Box, Divider, Paper, Portal, Stack, styled } from "@mui/material";
import { debounce } from "@mui/material/utils";
import Subscript from "@tiptap/extension-subscript";
import Superscript from "@tiptap/extension-superscript";
import TextAlign from "@tiptap/extension-text-align";
import type { Editor } from "@tiptap/react";
import { EditorContent, useEditor, useEditorState } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { useEffect, useRef, useState } from "react";

import { ICON_NAME } from "@p4b/ui/components/Icon";

import type { TextElementSchema } from "@/lib/validations/widget";

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

export const TipTapEditorContent = styled(EditorContent)(() => ({
  flexGrow: 1,
  height: "100%",
  overflow: "hidden",
  wordBreak: "break-word",
  overflowWrap: "break-word",
  "& .ProseMirror": {
    wordBreak: "break-word",
    overflowWrap: "break-word",
    padding: 0,
    margin: 0,
    height: "100%",
    boxSizing: "border-box",
    // Remove default margins from paragraphs and headings
    "& p, & h1, & h2, & h3, & h4, & h5, & h6": {
      margin: 0,
    },
    "& p:first-of-type, & h1:first-of-type, & h2:first-of-type, & h3:first-of-type": {
      marginTop: 0,
    },
  },
  "& > .ProseMirror-focused": {
    outline: "none",
  },
  "& > .ProseMirror:focus": {
    outline: "none",
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

  // Sync editor content when config changes (e.g., switching layouts)
  useEffect(() => {
    if (editor && config.setup.text !== undefined) {
      const currentContent = editor.getHTML();
      if (currentContent !== config.setup.text) {
        editor.commands.setContent(config.setup.text || "");
      }
    }
  }, [editor, config.setup.text]);

  return <TipTapEditorContent editor={editor} />;
};

const TextElementWidgetEditable = ({
  config,
  onWidgetUpdate,
}: {
  config: TextElementSchema;
  onWidgetUpdate?: (newConfig: TextElementSchema) => void;
}) => {
  const [isEditMode, setIsEditMode] = useState(false);
  const mouseDownPos = useRef<{ x: number; y: number } | null>(null);

  const editor = useEditor({
    extensions,
    content: config.setup.text || "",
    immediatelyRender: true,
    shouldRerenderOnTransaction: false,
    editable: isEditMode,
  });

  // Update editor editable state when isEditMode changes
  useEffect(() => {
    if (editor) {
      editor.setEditable(isEditMode);
    }
  }, [editor, isEditMode]);

  // Sync editor content when config changes (e.g., switching layouts)
  useEffect(() => {
    if (editor && config.setup.text !== undefined && !isEditMode) {
      const currentContent = editor.getHTML();
      if (currentContent !== config.setup.text) {
        editor.commands.setContent(config.setup.text || "");
      }
    }
  }, [editor, config.setup.text, isEditMode]);

  const [toolbarOpen, setToolbarOpen] = useState(false);
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null);

  useEffect(() => {
    if (!editor) return;

    const handleFocus = () => setToolbarOpen(true);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const handleBlur = ({ event }: any) => {
      if (event?.relatedTarget && (event.relatedTarget as HTMLElement).closest(".tiptap-toolbar")) return;
      setToolbarOpen(false);
      setIsEditMode(false);
    };

    editor.on("focus", handleFocus);
    editor.on("blur", handleBlur);

    return () => {
      editor.off("focus", handleFocus);
      editor.off("blur", handleBlur);
    };
  }, [editor]);

  // Handle mouse events to distinguish click from drag
  const handleMouseDown = (e: React.MouseEvent) => {
    mouseDownPos.current = { x: e.clientX, y: e.clientY };
  };

  const handleMouseUp = (e: React.MouseEvent) => {
    if (!mouseDownPos.current) return;

    // Calculate distance moved
    const dx = e.clientX - mouseDownPos.current.x;
    const dy = e.clientY - mouseDownPos.current.y;
    const distance = Math.sqrt(dx * dx + dy * dy);

    // If mouse moved less than 5px, it's a click - enable edit mode
    if (distance < 5 && !isEditMode) {
      setIsEditMode(true);
      // Focus editor after enabling edit mode
      setTimeout(() => {
        editor?.commands.focus();
      }, 0);
    }

    mouseDownPos.current = null;
  };

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

  const containerRef = useRef<HTMLDivElement>(null);
  const [toolbarPosition, setToolbarPosition] = useState({ top: 0, left: 0, width: 0 });

  // Update toolbar position continuously while open
  useEffect(() => {
    if (!toolbarOpen || !containerRef.current) return;

    const updatePosition = () => {
      const rect = containerRef.current?.getBoundingClientRect();
      if (rect) {
        setToolbarPosition({
          top: rect.top - 8,
          left: rect.left + rect.width / 2, // Center point
          width: rect.width,
        });
      }
    };

    updatePosition();

    // Use animation frame for smooth following during drag
    let animationId: number;
    const animate = () => {
      updatePosition();
      animationId = requestAnimationFrame(animate);
    };
    animationId = requestAnimationFrame(animate);

    return () => cancelAnimationFrame(animationId);
  }, [toolbarOpen]);

  return (
    <Box
      ref={containerRef}
      onMouseDown={handleMouseDown}
      onMouseUp={handleMouseUp}
      sx={{ height: "100%", width: "100%", cursor: isEditMode ? "text" : "default" }}>
      {/* Toolbar rendered via Portal to escape overflow:hidden */}
      {toolbarOpen && (
        <Portal>
          <Box
            className="tiptap-toolbar"
            onMouseDown={(e) => {
              e.stopPropagation();
            }}
            onMouseUp={(e) => e.stopPropagation()}
            onClick={(e) => e.stopPropagation()}
            onPointerDown={(e) => {
              e.stopPropagation();
            }}
            onPointerUp={(e) => e.stopPropagation()}
            onTouchStart={(e) => e.stopPropagation()}
            sx={{
              position: "fixed",
              top: toolbarPosition.top,
              left: toolbarPosition.left,
              transform: "translate(-50%, -100%)", // Center horizontally and position above
              zIndex: 1400,
              pointerEvents: "auto",
            }}>
            <ToolbarContainer>
              {editor && (
                <Stack direction="row" spacing={1} alignItems="center">
                  <BlockTypeSelect
                    editor={editor}
                    onOpen={() => setActiveDropdown("blockType")}
                    onClose={() => setActiveDropdown(null)}
                    forceClose={activeDropdown !== "blockType" && activeDropdown !== null}
                  />
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
                  <AlignSelect
                    editor={editor}
                    onOpen={() => setActiveDropdown("align")}
                    onClose={() => setActiveDropdown(null)}
                    forceClose={activeDropdown !== "align" && activeDropdown !== null}
                  />
                </Stack>
              )}
            </ToolbarContainer>
          </Box>
        </Portal>
      )}

      <TipTapEditorContent
        editor={editor}
        sx={{
          overflowY: isEditMode ? "auto" : "hidden",
          // Prevent text selection and let pointer events pass through when not in edit mode
          // This allows dragging the element without accidentally selecting text
          userSelect: isEditMode ? "auto" : "none",
          pointerEvents: isEditMode ? "auto" : "none",
          "& .ProseMirror": {
            userSelect: isEditMode ? "auto" : "none",
            pointerEvents: isEditMode ? "auto" : "none",
          },
        }}
      />
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
