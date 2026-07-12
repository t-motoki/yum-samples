// ESLint flat config。src と tests を対象にする。
import js from "@eslint/js";
import globals from "globals";

export default [
  { ignores: ["node_modules/**"] },

  js.configs.recommended,

  {
    files: ["src/**/*.js"],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "commonjs",
      globals: { ...globals.node },
    },
    rules: {
      "no-var": "error",
      eqeqeq: "error",
      "prefer-const": "error",
      "no-unused-vars": "error",
    },
  },

  {
    files: ["tests/**/*.js"],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "commonjs",
      globals: { ...globals.node, ...globals.jest },
    },
    rules: {
      "no-var": "error",
      eqeqeq: "error",
      "prefer-const": "error",
      "no-unused-vars": "error",
    },
  },
];
