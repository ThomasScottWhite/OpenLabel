import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import "bootstrap/dist/css/bootstrap.min.css";
import "./app.css";

import Home from "./Home.tsx";
import NotFound from "./NotFound.tsx";
import Login from "./Login.tsx";
import Projects from "./Projects.tsx";
import ProjectPage from "./ProjectPage.tsx";
import Annotator from "./Annotator.tsx";
import CreateAccount from "./CreateAccount.tsx";

function App() {
  document.body.setAttribute("data-bs-theme", "dark");

  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/create-account" element={<CreateAccount />} />
        <Route path="/projects" element={<Projects />} />
        <Route path="/projects/:id" element={<ProjectPage />} />
        <Route path="/projects/:id/annotator" element={<Annotator />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Router>
  );
}
export default App;
