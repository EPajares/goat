#!/bin/sh

# Replace placeholders with actual environment variables
for var in $(printenv | grep '^NEXT_PUBLIC' | cut -d= -f1); do
  value=$(printenv $var)
  echo "Replacing APP_$var with value: $value"
  find /app/apps/web/.next -type f -exec sed -i "s#APP_$var#$value#g" {} +
done

echo "Starting Nextjs"
exec "$@"
