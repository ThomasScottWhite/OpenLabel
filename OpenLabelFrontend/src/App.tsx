import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import "bootstrap/dist/css/bootstrap.min.css";

import Annotator from "./Annotator.tsx";
import Home from "./Home.tsx"; // A sample home page
import NotFound from "./NotFound.tsx"; // A 404 Not Found page
import Login from "./Login.tsx";
import Projects from "./Projects.tsx";
import ProjectPage from "./ProjectPage.tsx";

function App() {
  document.body.setAttribute("data-bs-theme", "dark");

  return (
    <Router>
      <div className="mw-100 mh-100">
        <div className="w-75 h-50 mx-auto">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login />} />
            <Route path="/annotator" element={<Annotator />} />
            <Route path="/projects" element={<Projects />} />
            <Route path="/projects/:id" element={<ProjectPage />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
