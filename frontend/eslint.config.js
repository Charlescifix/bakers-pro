import js from '@eslint/js';

export default [
  {
    ignores: [
      'dist/**',
      'node_modules/**',
      'src/**/*.ts',
      'src/**/*.tsx',
      'vite.config.ts',
      'tsconfig.tsbuildinfo',
    ],
  },
  js.configs.recommended,
];
