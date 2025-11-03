import { useTranslation } from "@/i18n/client";

import type { FeatureLayerProperties, LayerFieldType } from "@/lib/validations/layer";

import LayerFieldSelector from "@/components/map/common/LayerFieldSelector";
import SectionOptions from "@/components/map/panels/common/SectionOptions";
import MarkerSelector from "@/components/map/panels/style/classification/MarkerSelector";
import MarkerIconPicker from "@/components/map/panels/style/marker/MarkerIconPicker";

const MarkerOptions = ({
  type,
  layerStyle,
  active,
  layerId,
  layerFields,
  selectedField,
  collapsed,
  onStyleChange,
}: {
  type: "marker";
  layerStyle?: FeatureLayerProperties;
  active: boolean;
  selectedField?: LayerFieldType;
  layerId: string;
  layerFields: LayerFieldType[];
  collapsed?: boolean;
  onStyleChange?: (newStyle: FeatureLayerProperties) => void;
}) => {
  const { t } = useTranslation("common");

  return (
    <SectionOptions
      active={!!active}
      baseOptions={
        <MarkerIconPicker
          selectedMarker={{
            name: layerStyle?.[`${type}`]?.["name"] || t("select_marker"),
            url: layerStyle?.[`${type}`]?.["url"] || "",
            category: layerStyle?.[`${type}`]?.["category"] || "",
            source: layerStyle?.[`${type}`]?.["source"] || "custom",
            id: layerStyle?.[`${type}`]?.["id"] || "",
          }}
          label={t("single_marker")}
          onSelectMarker={(marker) => {
            const newStyle = JSON.parse(JSON.stringify(layerStyle)) || {};
            newStyle[`${type}`] = {
              name: marker.name,
              url: marker.url,
              category: marker.category,
              source: marker.source,
              id: marker.id,
            };
            if (onStyleChange) {
              onStyleChange(newStyle);
            }
          }}
        />
      }
      advancedOptions={
        <>
          <LayerFieldSelector
            fields={layerFields.filter((f) => f.type === "string")}
            selectedField={selectedField}
            setSelectedField={(field) => {
              const newStyle = JSON.parse(JSON.stringify(layerStyle)) || {};
              newStyle[`${type}_field`] = field;
              if (onStyleChange) {
                onStyleChange(newStyle);
              }
            }}
            label={t("marker_based_on")}
            tooltip={t("marker_based_on_desc")}
          />

          {layerStyle?.[`custom_${type}`] && layerStyle?.[`${type}_field`] && (
            <MarkerSelector
              markerMaps={layerStyle?.[`${type}_mapping`] || []}
              onCustomApply={(markerMaps) => {
                const newStyle = JSON.parse(JSON.stringify(layerStyle)) || {};
                newStyle[`${type}_mapping`] = markerMaps;
                if (onStyleChange) {
                  onStyleChange(newStyle);
                }
              }}
              label={t("ordinal_marker")}
              activeLayerId={layerId}
              activeLayerField={layerStyle[`${type}_field`] || { name: "", type: "string" }}
            />
          )}
        </>
      }
      collapsed={collapsed}
    />
  );
};

export default MarkerOptions;
