#!/usr/bin/env bash

set -e
set -x


pnpm run typecheck
pnpm run lint:report

# Combine all the lint results into a single file for easy viewing or annotate to the PR
jq -s '[.[]]|flatten' lint-results/*.json &> lint-results/eslint_report.json

