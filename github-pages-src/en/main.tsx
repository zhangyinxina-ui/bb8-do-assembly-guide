import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import EnglishPage from "../../app/EnglishPage";
import "../../app/globals.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <EnglishPage />
  </StrictMode>,
);
