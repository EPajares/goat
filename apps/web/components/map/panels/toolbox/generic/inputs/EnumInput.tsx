/**
 * Generic Enum Input Component
 *
 * Renders a dropdown selector for enum values from OGC process schema.
 */
import { useMemo } from "react";

import { formatInputName } from "@/lib/utils/ogc-utils";

import type { SelectorItem } from "@/types/map/common";
import type { ProcessedInput } from "@/types/map/ogc-processes";

import Selector from "@/components/map/panels/common/Selector";

interface EnumInputProps {
  input: ProcessedInput;
  value: string | number | boolean | undefined;
  onChange: (value: string | number | boolean | undefined) => void;
  disabled?: boolean;
}

export default function EnumInput({ input, value, onChange, disabled }: EnumInputProps) {
  // Convert enum values to selector items
  const enumItems: SelectorItem[] = useMemo(() => {
    if (!input.enumValues) return [];

    return input.enumValues.map((enumValue) => ({
      value: enumValue as string | number,
      label: formatInputName(String(enumValue)),
    }));
  }, [input.enumValues]);

  // Find selected item
  const selectedItem = useMemo(() => {
    if (value === undefined || value === null) return undefined;
    return enumItems.find((item) => item.value === value);
  }, [value, enumItems]);

  const handleChange = (item: SelectorItem | SelectorItem[] | undefined) => {
    if (Array.isArray(item)) {
      onChange(item[0]?.value as string | number | undefined);
    } else {
      onChange(item?.value as string | number | undefined);
    }
  };

  return (
    <Selector
      selectedItems={selectedItem}
      setSelectedItems={handleChange}
      items={enumItems}
      label={input.title}
      tooltip={input.description}
      placeholder={`Select ${input.title.toLowerCase()}`}
      disabled={disabled}
    />
  );
}
