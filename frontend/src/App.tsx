import React, { useEffect, useState } from "react";
import { Navbar } from "./components/Navbar";
import { Footer } from "./components/Footer";
import { LandingPage } from "./pages/LandingPage";
import { EstimatePage } from "./pages/EstimatePage";
import { CheckPage } from "./pages/CheckPage";
import { DocsPage } from "./pages/DocsPage";
import { APP_CONFIG } from "./config";

export const App: React.FC = () => {
  const [currentPath, setCurrentPath] = useState<string>(window.location.pathname || "/");
  const [searchParams, setSearchParams] = useState<URLSearchParams>(
    new URLSearchParams(window.location.search)
  );

  useEffect(() => {
    const handlePopState = () => {
      setCurrentPath(window.location.pathname || "/");
      setSearchParams(new URLSearchParams(window.location.search));
    };

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  const navigateTo = (pathAndQuery: string) => {
    const [path, query] = pathAndQuery.split("?");
    window.history.pushState({}, "", pathAndQuery);
    setCurrentPath(path || "/");
    setSearchParams(new URLSearchParams(query || ""));
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const updateUrlParams = (date: string, percentile: number) => {
    const newParams = new URLSearchParams(window.location.search);
    newParams.set("date", date);
    newParams.set("percentile", percentile.toString());
    const newUrl = `${window.location.pathname}?${newParams.toString()}`;
    window.history.replaceState({}, "", newUrl);
    setSearchParams(newParams);
  };

  const selectedDate = searchParams.get("date") || APP_CONFIG.defaultDecisionDate;
  const selectedPercentile = Number(searchParams.get("percentile")) || APP_CONFIG.defaultPercentile;

  const renderContent = () => {
    if (currentPath === "/jan25/check") {
      return (
        <CheckPage
          initialDate={selectedDate}
          initialPercentile={selectedPercentile}
          onNavigate={navigateTo}
          updateUrl={updateUrlParams}
        />
      );
    }

    if (currentPath === "/jan25") {
      return (
        <EstimatePage
          initialDate={selectedDate}
          initialPercentile={selectedPercentile}
          onNavigate={navigateTo}
          updateUrl={updateUrlParams}
        />
      );
    }

    if (currentPath === "/docs") {
      return <DocsPage />;
    }

    // Default to Landing Page
    return <LandingPage onNavigate={navigateTo} />;
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 font-sans">
      <Navbar currentPath={currentPath} onNavigate={navigateTo} />
      <main className="flex-1">{renderContent()}</main>
      <Footer />
    </div>
  );
};
