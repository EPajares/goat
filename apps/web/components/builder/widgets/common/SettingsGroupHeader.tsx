import { Divider, Typography } from "@mui/material";
import React from "react";

interface SettingsGroupHeaderProps {
  label: string;
}

export const SettingsGroupHeader: React.FC<SettingsGroupHeaderProps> = ({ label }) => (
  <>
    <Typography sx={{ mb: 1, fontWeight: "bold" }}>{label}</Typography>
    <Divider sx={{ mt: 0, mb: 4 }} />
  </>
);

export default SettingsGroupHeader;
