import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import GenesisChat from "./GenesisChat";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <GenesisChat />
  </StrictMode>,
);
