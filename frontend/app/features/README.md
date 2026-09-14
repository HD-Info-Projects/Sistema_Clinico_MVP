# Frontend Features

This directory is the migration target for domain-oriented frontend code.

Nuxt conventions remain in place:

- `app/pages` keeps route files.
- `app/layouts` keeps Nuxt layouts.
- `app/middleware` keeps route middleware.
- `app/assets` keeps static application assets.

Create feature subdirectories only when moving real code for that domain. Do
not add empty `components`, `composables`, `services`, `stores`, `types`, or
`utils` folders just to match a template.

Initial target domains identified in the current codebase:

- `auth`
- `usuarios`
- `unidades`
- `pacientes`
- `agenda`
- `atendimentos`
- `recepcao`
- `clinico`
- `exames`
- `procedimentos`
- `documentos`
- `chamadas`
- `lgpd`
