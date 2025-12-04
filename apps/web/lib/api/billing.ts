import useSWR from "swr";

import { fetcher } from "@/lib/api/fetcher";
import type { PlansList } from "@/lib/validations/billing";

const ACCOUNTS_BASE = process.env.NEXT_PUBLIC_ACCOUNTS_API_URL;
export const ACCOUNTS_ENABLED = Boolean(ACCOUNTS_BASE);

export const BILLING_API_BASE_URL = ACCOUNTS_ENABLED ? new URL("api/v1/billing", ACCOUNTS_BASE!).href : "";

// If your PlansList isn't an array, adjust this stub accordingly.
const STUB_PLANS = [] as unknown as PlansList;

export const useAppPlans = () => {
  const disabled = !ACCOUNTS_ENABLED;

  const { data, isLoading, error, mutate, isValidating } = useSWR<PlansList>(
    disabled ? null : `${BILLING_API_BASE_URL}/plans`,
    fetcher,
    {
      revalidateOnFocus: !disabled,
      revalidateOnReconnect: !disabled,
      shouldRetryOnError: !disabled,
    }
  );

  return {
    plans: data ?? STUB_PLANS,
    isLoading,
    isError: error,
    mutate,
    isValidating,
  };
};
