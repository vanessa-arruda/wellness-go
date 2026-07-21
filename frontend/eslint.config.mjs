import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    rules: {
      // Prettier's printWidth only reformats breakable code — it leaves
      // comments and unbreakable strings untouched. This is the hard,
      // unconditional 120-char limit (matches backend's ruff E501).
      "max-len": ["error", { code: 120, ignoreUrls: true }],
    },
  },
  {
    // shadcn/ui vendored components — long Tailwind className strings are
    // expected here and not meant to be manually wrapped.
    files: ["src/components/ui/**"],
    rules: {
      "max-len": "off",
    },
  },
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
]);

export default eslintConfig;
