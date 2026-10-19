import { Routes, Route } from "react-router-dom";
import AuthModal from "./components/AuthModal";
import Landing from "./pages/Landing";
import Workspace from "./pages/Workspace";

export default function App() {
  return (
    <>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/app/*" element={<Workspace />} />
      </Routes>
      <AuthModal />
    </>
  );
}