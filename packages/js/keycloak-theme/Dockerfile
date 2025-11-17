# build environment
FROM node:14-alpine as build
WORKDIR /app
COPY package.json ./
RUN pnpm install
COPY . .
RUN pnpm build

# production environment
FROM nginx:stable-alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY --from=build /app/nginx.conf /etc/nginx/conf.d/default.conf
CMD nginx -g 'daemon off;'
