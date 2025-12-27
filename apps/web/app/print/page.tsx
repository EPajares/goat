/**
 * Print setup page - Used by Playwright to inject authentication token.
 *
 * This page serves as a landing page where Playwright can:
 * 1. Navigate to first (to establish the origin)
 * 2. Inject the access token into localStorage
 * 3. Then navigate to the actual print page (/print/[projectId]/[layoutId])
 *
 * This page is not meant to be accessed directly by users.
 */
export default function PrintSetupPage() {
  return (
    <div
      style={{
        width: "100vw",
        height: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: "#fff",
        color: "#666",
        fontFamily: "sans-serif",
      }}>
      <p>Preparing print...</p>
    </div>
  );
}
