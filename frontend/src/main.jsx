import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { AuthProvider } from "./AuthContext.jsx";
import App from "./App.jsx";
import "./index.css";
import { CodebaseProvider } from "./CodebaseContext.jsx";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <CodebaseProvider>
          <App />
        </CodebaseProvider>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>
);