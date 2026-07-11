import tseslint from "typescript-eslint";

export default tseslint.config(
  {
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      parser: tseslint.parser,
      parserOptions: {
        ecmaFeatures: { jsx: true },
        project: ["./tsconfig.json"],
        tsconfigRootDir: import.meta.dirname,
      },
    },
    rules: {
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            // entities: только public API @/entities, не внутренние слайсы
            {
              group: ["@/entities/*/**"],
              message:
                "Импорт из entities разрешен только через @/entities (public API). Не импортируйте внутренние слайсы напрямую.",
            },
            // features: не импортировать внутренние слои напрямую
            {
              group: ["@/features/*/api/**"],
              message: "API слой фичи не должен импортироваться напрямую. Используйте public API фичи (@/features/xxx).",
            },
            {
              group: ["@/features/*/model/**"],
              message: "Model слой фичи не должен импортироваться напрямую. Используйте public API фичи.",
            },
            // features UI можно импортировать в widgets (FSD pattern)
            // shared: не импортировать внутренние файлы сегментов, только public API сегментов
            {
              group: ["@/shared/api/*/**"],
              message: "Импорт из shared/api разрешен только через @/shared/api (public API).",
            },
            {
              group: ["@/shared/config/*/**"],
              message: "Импорт из shared/config разрешен только через @/shared/config (public API).",
            },
            {
              group: ["@/shared/lib/*/**"],
              message: "Импорт из shared/lib разрешен только через @/shared/lib (public API).",
            },
            {
              group: ["@/shared/types/*/**"],
              message: "Импорт из shared/types разрешен только через @/shared/types (public API).",
            },
            {
              group: ["@/shared/ui/*/**"],
              message: "Импорт из shared/ui разрешен только через @/shared/ui (public API).",
            },
            // widgets: не импортировать внутренние UI виджетов напрямую
            {
              group: ["@/widgets/*/ui/**"],
              message: "UI виджетов не должен импортироваться напрямую. Используйте public API виджета (@/widgets/xxx).",
            },
          ],
        },
      ],
    },
  },
);