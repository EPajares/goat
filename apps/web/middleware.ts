import { stackMiddlewares } from "@/middlewares/stackMiddlewares";
import { withAuth } from "@/middlewares/withAuth";
import { withLegacyRedirect } from "@/middlewares/withLegacyRedirect";
import { withOrganization } from "@/middlewares/withOrganization";

export default stackMiddlewares([withLegacyRedirect, withAuth, withOrganization]);
