import { redirect } from "next/navigation";

export default async function Account({}) {
  return redirect("/settings/account/profile");
}
