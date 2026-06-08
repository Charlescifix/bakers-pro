import js from '@eslint/js';

export default [
  {
    ignores: ['dist/**', 'node_modules/**', 'tsconfig.tsbuildinfo'],
  },
  {
    files: ['**/*.{js,jsx}'],
    ...js.configs.recommended,
  },
];
