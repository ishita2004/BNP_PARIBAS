import React from "react";

export default function GraphDisplay({ base64 }) {
  if (!base64) return null;
  return (
    <div style={{ marginTop: "10px" }}>
      <img src={`data:image/png;base64,${base64}`} alt="Graph" />
    </div>
  );
}
