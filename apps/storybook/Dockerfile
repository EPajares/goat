FROM node:22-alpine AS installer
RUN npm install -g corepack@latest
RUN corepack enable && corepack prepare pnpm@8.6.0 --activate

WORKDIR /app

COPY . .

RUN pnpm install

# Build the project
RUN pnpm turbo run build --filter=storybook

# production stage
FROM nginx:stable-alpine as production-stage
# mkdir called storybook in /usr/share/nginx/html
RUN mkdir /usr/share/nginx/html/storybook
COPY --from=installer /app/apps/storybook/storybook-static /usr/share/nginx/html/storybook
COPY --from=installer /app/apps/storybook/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
