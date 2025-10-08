import { redirect } from "next/navigation";

export default async function Organization({}) {
  return redirect("/settings/organization/profile");
}
