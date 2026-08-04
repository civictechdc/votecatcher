FROM oven/bun:1.3.14@sha256:e10577f0db68676a7024391c6e5cb4b879ebd17188ab750cf10024a6d700e5c4 AS base
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
