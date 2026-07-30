# syntax=docker/dockerfile:1
FROM node:22-alpine AS build

WORKDIR /app

ENV NUXT_TELEMETRY_DISABLED=1 \
    NODE_OPTIONS=--max-old-space-size=4096 \
    PNPM_HOME=/pnpm

ENV PATH=${PNPM_HOME}:${PATH}

RUN corepack enable && corepack prepare pnpm@10.33.4 --activate

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./

RUN --mount=type=cache,id=pnpm-store,target=/pnpm/store \
    pnpm install --frozen-lockfile

COPY . .
RUN pnpm build

FROM node:22-alpine AS runtime

WORKDIR /app

ENV NODE_ENV=production \
    NITRO_HOST=0.0.0.0 \
    NITRO_PORT=3000 \
    NUXT_TELEMETRY_DISABLED=1

COPY --from=build --chown=node:node /app/.output ./.output

USER node

EXPOSE 3000

CMD ["node", ".output/server/index.mjs"]
