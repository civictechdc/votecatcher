FROM oven/bun:1 AS base
WORKDIR /app

RUN echo "deb http://deb.debian.org/debian-security trixie-security main" > /etc/apt/sources.list.d/trixie-security.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends libssl3t64 openssl-provider-legacy \
    && rm -rf /var/lib/apt/lists/* /etc/apt/sources.list.d/trixie-security.list

FROM base AS deps
COPY package.json bun.lock* ./
RUN bun install --frozen-lockfile --production

FROM base AS dev
COPY --from=deps /app/node_modules ./node_modules
COPY . .

EXPOSE 5173

CMD ["bun", "run", "dev", "--host"]
