import React from "react";
import FileUpload from "./components/FileUpload";
import Chatbot from "./components/Chatbot";

function App() {
  return (
    <div style={{ padding: "20px" }}>
      <h1>Customer Data NLP Dashboard</h1>
      <FileUpload />
      <hr />
      <Chatbot />
    </div>
  );
}

export default App;
