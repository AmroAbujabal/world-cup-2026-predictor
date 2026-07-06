import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
// Self-hosted sport/esport type pairing (CSP-safe, no runtime network)
import "@fontsource/russo-one/400.css";
import "@fontsource/chakra-petch/400.css";
import "@fontsource/chakra-petch/500.css";
import "@fontsource/chakra-petch/600.css";
import "@fontsource/chakra-petch/700.css";
import "./index.css";
import App from "./App.jsx";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
