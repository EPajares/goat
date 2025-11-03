import type { FormatNumberTypes } from "@/lib/validations/widget";

export const formatNumber = (
  value: number,
  format?: FormatNumberTypes,
  language: string = 'en-US'
): string => {
  if (!format) return new Intl.NumberFormat(language).format(value);
  const formatterOptions: Record<FormatNumberTypes, Intl.NumberFormatOptions> = {
    none: {},
    integer: { maximumFractionDigits: 0, useGrouping: false },
    grouping: { maximumFractionDigits: 0 },
    grouping_2d: { minimumFractionDigits: 2, maximumFractionDigits: 2 },
    signed_2d: {
      signDisplay: 'always',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    },
    compact: {
      notation: 'compact',
      compactDisplay: 'short'
    },
    compact_1d: {
      notation: 'compact',
      compactDisplay: 'short',
      minimumFractionDigits: 1,
      maximumFractionDigits: 1
    },
    decimal_2: { minimumFractionDigits: 2, maximumFractionDigits: 2 },
    decimal_3: { minimumFractionDigits: 3, maximumFractionDigits: 3 },
    decimal_max: { maximumFractionDigits: 3 },
    currency_usd: { style: 'currency', currency: 'USD' },
    currency_eur: { style: 'currency', currency: 'EUR' },
    percent: { style: 'percent', maximumFractionDigits: 0 },
    percent_1d: { style: 'percent', minimumFractionDigits: 1, maximumFractionDigits: 1 },
    percent_2d: { style: 'percent', minimumFractionDigits: 2, maximumFractionDigits: 2 }
  };

  try {
    return new Intl.NumberFormat(language, formatterOptions[format]).format(value);
  } catch (e) {
    console.error('Formatting error:', e);
    return new Intl.NumberFormat(language).format(value);
  }
};
