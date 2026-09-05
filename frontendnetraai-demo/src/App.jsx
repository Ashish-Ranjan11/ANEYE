import { useState } from "react";
import { Routes, Route, useLocation } from "react-router-dom";

import LandingPage from "./pages/LandingPage";
import EnginePage from "./pages/EnginePage";
import LaunchScreen from "./components/LaunchScreen";

export default function App() {
  const location = useLocation();

  const [showLaunch, setShowLaunch] = useState(
    location.pathname === "/"
  );

  return (
    <>
      {showLaunch && (
        <LaunchScreen
          onComplete={() => setShowLaunch(false)}
        />
      )}

      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/engine" element={<EnginePage />} />
      </Routes>
    </>
  );
}
