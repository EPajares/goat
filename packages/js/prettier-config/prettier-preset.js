module.exports = {
  bracketSpacing: true,
  bracketSameLine: true,
  singleQuote: false,
  jsxSingleQuote: false,
  trailingComma: "es5",
  semi: true,
  printWidth: 110,
  arrowParens: "always",
  importOrder: ["<THIRD_PARTY_MODULES>", "^@p4b/ui/(.*)$", "@p4b/(.*)$", "^@/i18n/(.*)$", "^@/lib/(.*)$", "^@/types(.*)$", "^@/hooks/(.*)$", "^@/components/(.*)$", "^@/(.*)$", "^[./]"],
  plugins: ["@trivago/prettier-plugin-sort-imports"],
  importOrderSeparation: true,
  importOrderSortSpecifiers: true,
};
