import { useState } from "react";
import "bootstrap/dist/css/bootstrap.min.css";
import Annotator from "./Annotator";
function App() {
  document.body.setAttribute("data-bs-theme", "dark");

  return (
    <div className="mw-100 mh-100">
      <div className="w-75 h-50 mx-auto">
        <Annotator></Annotator>
      </div>
    </div>
  );
}

export default App;
