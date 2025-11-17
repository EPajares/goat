import { Card, CardContent, Stack, Typography, useTheme } from "@mui/material";
export default function AuthContainer({
  headerTitle,
  headerAlert,
  body,
  footer,
  otherFooterActions,
}: {
  headerTitle: React.ReactNode;
  headerAlert?: React.ReactNode;
  body: React.ReactNode;
  footer?: React.ReactNode;
  otherFooterActions?: React.ReactNode;
}) {
  const theme = useTheme();

  return (
    <Card
      sx={{
        width: 490,
        height: "fit-content",
        marginBottom: theme.spacing(4),
      }}
    >
      <CardContent>
        <Stack
          spacing={theme.spacing(4)}
          sx={{
            mb: theme.spacing(4),
            textAlign: "center",
          }}
        >
          <Typography
            variant="h5"
            sx={{
              pb: theme.spacing(4),
            }}
          >
            {/* Title */}
            {headerTitle}
          </Typography>
          {/* Alert message*/}
          {headerAlert}
        </Stack>
        {/* Main Body*/}
        {body}
        {/* For links displayed under main body (e.g New User ? Create Accounts) */}
        {footer}
      </CardContent>
      {otherFooterActions && (
        <Stack
          justifyContent="flex-end"
          direction="row"
          spacing={theme.spacing(2)}
          sx={{
            pb: theme.spacing(2),
            px: theme.spacing(4),
          }}
        >
          {/* For other actions such as language selection, theme etc. */}
          {otherFooterActions}
        </Stack>
      )}
    </Card>
  );
}
