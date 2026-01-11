import {
  Box,
  Button,
  Card,
  CardContent,
  CardMedia,
  Divider,
  Grid,
  Skeleton,
  Stack,
  Typography,
  useTheme,
} from "@mui/material";
import { useTranslation } from "react-i18next";

import { ICON_NAME, Icon } from "@p4b/ui/components/Icon";

type BlogPost = {
  title: string;
  date: string;
  thumbnail: string;
  url: string;
};

const blogPostsEnglish: BlogPost[] = [
  {
    title: 'GOAT 2.2.0 "Cashmere" is here',
    date: "December 16, 2025",
    thumbnail:
      "https://cdn.prod.website-files.com/6554ce5f672475c1f40445af/693fb15bef07eb7497624d4d_GOAT_new-version_cover-p-1600.webp",
    url: "https://www.plan4better.de/en/post/goat-2-2-0-cashmere-is-here",
  },
  {
    title: 'GOAT 2.1.0 "Ibex" is here',
    date: "October 21, 2025",
    thumbnail:
      "https://cdn.prod.website-files.com/6554ce5f672475c1f40445af/68ef733d034dbecbd08cc8f3_dashboard-builder-p-1600.webp",
    url: "https://www.plan4better.de/en/post/goat-2-1-0-ibex-is-here",
  },
  {
    title: "GOAT v2 is here!",
    date: "September 19, 2024",
    thumbnail:
      "https://cdn.prod.website-files.com/6554ce5f672475c1f40445af/66eaa2b28eb3db409d799756_Blogpost_17.09.2024.%20GOAT%20v2%20announcement.png",
    url: "https://www.plan4better.de/en/post/goat-v2-is-here",
  },
];

const blogPostsGerman: BlogPost[] = [
  {
    title: 'GOAT 2.2.0 „Cashmere" ist da',
    date: "16. Dezember 2025",
    thumbnail:
      "https://cdn.prod.website-files.com/6554ce5f672475c1f40445af/693fb15bef07eb7497624d4d_GOAT_new-version_cover-p-1600.webp",
    url: "https://www.plan4better.de/de/post/goat-2-2-0-cashmere-ist-da",
  },
  {
    title: 'GOAT 2.1.0 "Ibex" ist da',
    date: "21. Oktober 2025",
    thumbnail:
      "https://cdn.prod.website-files.com/6554ce5f672475c1f40445af/68ef733d034dbecbd08cc8f3_dashboard-builder-p-1600.webp",
    url: "https://www.plan4better.de/de/post/goat-2-1-0-ibex-is-here",
  },
  {
    title: "GOAT v2 ist da!",
    date: "19. September 2024",
    thumbnail:
      "https://cdn.prod.website-files.com/6554ce5f672475c1f40445af/66eaa2b28eb3db409d799756_Blogpost_17.09.2024.%20GOAT%20v2%20announcement.png",
    url: "https://www.plan4better.de/de/post/goat-v2-is-here",
  },
];

const BlogSection = () => {
  const isLoading = false;
  const theme = useTheme();
  const { t, i18n } = useTranslation("common");

  return (
    <Box>
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: 2,
        }}>
        <Typography variant="h6">{t("explore")}</Typography>
        <Button
          variant="text"
          size="small"
          endIcon={<Icon iconName={ICON_NAME.EXTERNAL_LINK} style={{ fontSize: 12 }} />}
          onClick={() =>
            window.open(
              i18n.language === "de"
                ? "https://www.plan4better.de/de/blog"
                : "https://www.plan4better.de/blog",
              "_blank"
            )
          }
          sx={{
            borderRadius: 0,
          }}>
          {t("visit_blog")}
        </Button>
      </Box>
      <Divider sx={{ mb: 4 }} />
      <Grid container spacing={5}>
        {(isLoading
          ? Array.from(new Array(3))
          : i18n.language === "de"
            ? blogPostsGerman
            : (blogPostsEnglish ?? [])
        ).map((item: BlogPost, index: number) => (
          <Grid
            item
            key={item?.title ?? index}
            xs={12}
            sm={6}
            md={6}
            lg={4}
            display={{
              sm: index > 3 ? "none" : "block",
              md: index > 3 ? "none" : "block",
              lg: index > 2 ? "none" : "block",
            }}>
            {!item ? (
              <Skeleton variant="rectangular" height={220} />
            ) : (
              <Card
                style={{
                  backgroundColor: "transparent",
                  border: "none",
                  boxShadow: "none",
                }}
                variant="outlined"
                onClick={() => window.open(item.url, "_blank")}
                sx={{
                  height: "100%",
                  display: "flex",
                  flexDirection: "column",
                  "&:hover": {
                    cursor: "pointer",
                    "& img": {
                      boxShadow: theme.shadows[4],
                    },
                    "& p": {
                      color: theme.palette.primary.main,
                    },
                  },
                }}>
                {item.thumbnail && (
                  <CardMedia
                    component="img"
                    sx={{
                      height: 220,
                      objectFit: "cover",
                      backgroundSize: "cover",
                      transition: theme.transitions.create(["box-shadow", "transform"], {
                        duration: theme.transitions.duration.standard,
                      }),
                    }}
                    image={item.thumbnail}
                  />
                )}
                <CardContent sx={{ flexGrow: 1, px: 0 }}>
                  <Stack spacing={2}>
                    <Typography gutterBottom variant="caption">
                      {item.date}
                    </Typography>

                    <Typography
                      sx={{
                        transition: theme.transitions.create(["color", "transform"], {
                          duration: theme.transitions.duration.standard,
                        }),
                      }}
                      fontWeight="bold">
                      {item.title}
                    </Typography>
                  </Stack>
                </CardContent>
              </Card>
            )}
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default BlogSection;
