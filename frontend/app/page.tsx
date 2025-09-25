"use client";

import { useState } from "react";
import SynphoraPage from "./synphora";
import WelcomePage from "./welcome";

enum CurrentPage {
  WELCOME = "welcome",
  MAIN = "main",
}

export default function Home() {
  const [currentPage, setCurrentPage] = useState<CurrentPage>(
    CurrentPage.WELCOME
  );

  // 如果需要跳过欢迎页面，则定义环境变量 NEXT_PUBLIC_SKIP_WELCOME 为 true
  const skipWelcome = process.env.NEXT_PUBLIC_SKIP_WELCOME === "true";

  if (skipWelcome) {
    return <SynphoraPage />;
  }

  const onWelcomeComplete = () => {
    setCurrentPage(CurrentPage.MAIN);
  };

  if (currentPage === CurrentPage.WELCOME) {
    return <WelcomePage onWelcomeComplete={onWelcomeComplete} />;
  } else if (currentPage === CurrentPage.MAIN) {
    return <SynphoraPage />;
  } else {
    throw new Error("Invalid current page");
  }
}
