import React from "react";

export default function ResultTable({ data }) {
  if (!data || !data.length) return <p>No data available</p>;

  const columns = Object.keys(data[0]);
  return (
    <table border="1" cellPadding="5" style={{ marginTop: "10px" }}>
      <thead>
        <tr>
          {columns.map((col) => (
            <th key={col}>{col}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {data.map((row, idx) => (
          <tr key={idx}>
            {columns.map((col) => (
              <td key={col}>{row[col]}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
