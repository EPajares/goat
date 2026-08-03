import { stackMiddlewares } from "@/middlewares/stackMiddlewares";
import { withAuth } from "@/middlewares/withAuth";
import { withCustomDomain } from "@/middlewares/withCustomDomain";
import { withLegacyRedirect } from "@/middlewares/withLegacyRedirect";
import { withOrganization } from "@/middlewares/withOrganization";

// Order: custom-domain rewrite must run BEFORE withAuth so the rewritten
// /map/public/<id> path hits withAuth's publicPaths exemption.
export default stackMiddlewares([
  withCustomDomain,
  withLegacyRedirect,
  withAuth,
  withOrganization,
]);
