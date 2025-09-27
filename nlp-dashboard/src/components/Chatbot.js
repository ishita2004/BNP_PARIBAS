import React, { useState } from "react";
import { askQuery } from "../api";
import ResultTable from "./ResultTable";
import GraphDisplay from "./GraphDisplay";

export default function Chatbot() {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState(null);

  const handleAsk = async () => {
    if (!query) return;
    try {
      const res = await askQuery(query);
      setResponse(res.data);
    } catch (err) {
      setResponse({ error: err.message });
    }
  };

  return (
    <div>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Ask anything about customer data..."
        style={{ width: "60%" }}
      />
      <button onClick={handleAsk}>Ask</button>

      {response && (
        <div>
          {response.error && <p style={{ color: "red" }}>{response.error}</p>}
          {response.result && <ResultTable data={response.result} />}
          {response.graph_base64 && <GraphDisplay base64={response.graph_base64} />}
        </div>
      )}
    </div>
  );
}
