"use client";

import { de, enUS } from "date-fns/locale";
import { useTranslation } from "react-i18next";

export function useDateFnsLocale() {
  const { i18n } = useTranslation();
  return i18n?.language === "de" ? de : enUS;
}
