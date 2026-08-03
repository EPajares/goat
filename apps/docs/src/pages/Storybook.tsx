import React from "react";
import clsx from "clsx";
import Link from "@docusaurus/Link";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import Layout from "@theme/Layout";

import styles from "./index.module.css";

export default function Storybook(): React.JSX.Element {
  const { siteConfig } = useDocusaurusContext();
  return (
    <Layout
      title={`Hello from ${siteConfig.title}`}
      description="Description will go into a meta tag in <head />"
    >
      <main>
        <div style={{height: '100vh'}}>
          <iframe
            src="https://v2.goat.plan4better.de/storybook" // iframe.html?id=shadowboxcta--docs&viewMode=docs&shortcuts=false&singleStory=true
            style={{overflow: 'hidden', overflowX: 'hidden', overflowY: 'hidden', height: '100%', width: '100%'}}
            width="100%"
            height="100vh"
          ></iframe>
        </div>
      </main>
    </Layout>
  );
}
