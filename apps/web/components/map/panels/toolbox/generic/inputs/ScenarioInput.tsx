/**
 * Scenario Input Component
 *
 * Renders a scenario selector dropdown that shows available scenarios
 * for the current project.
 */
import { useParams } from "next/navigation";
import { useTranslation } from "react-i18next";

import { ICON_NAME } from "@p4b/ui/components/Icon";

import type { SelectorItem } from "@/types/map/common";
import type { ProcessedInput } from "@/types/map/ogc-processes";

import { useScenarioItems } from "@/hooks/map/ToolsHooks";

import Selector from "@/components/map/panels/common/Selector";

interface ScenarioInputProps {
  input: ProcessedInput;
  value: string | undefined;
  onChange: (value: string | null) => void;
  disabled?: boolean;
}

export default function ScenarioInput({ input, value, onChange, disabled }: ScenarioInputProps) {
  const { t } = useTranslation("common");
  const { projectId } = useParams();

  // Get scenario items for this project
  const { scenarioItems } = useScenarioItems(projectId as string);

  // Find selected item
  const selectedItem = scenarioItems.find((item) => item.value === value);

  const handleChange = (item: SelectorItem[] | SelectorItem | undefined) => {
    if (!item || Array.isArray(item)) {
      onChange(null);
    } else {
      onChange(item.value as string);
    }
  };

  // Get label from uiMeta or fallback to title
  const label = input.uiMeta?.label || input.title || t("scenario");

  return (
    <Selector
      selectedItems={selectedItem}
      setSelectedItems={handleChange}
      items={scenarioItems}
      label={label}
      placeholder={t("select_scenario")}
      tooltip={input.description || t("choose_scenario")}
      disabled={disabled || scenarioItems.length === 0}
      emptyMessage={t("no_scenarios_created")}
      emptyMessageIcon={ICON_NAME.SCENARIO}
    />
  );
}
