import React, { Suspense } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const App = React.lazy(() => import("./App").then((module) => ({ default: module.App })));

createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <Suspense fallback={<div className="app-loading">Loading local studio...</div>}>
      <App />
    </Suspense>
  </React.StrictMode>
);
