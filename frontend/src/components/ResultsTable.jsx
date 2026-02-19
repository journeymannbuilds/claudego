import React from "react";
import "./ResultsTable.css";

function ResultsTable({ data }) {
  if (!data || !data.columns || !data.rows) {
    return null;
  }

  return (
    <div className="results-container">
      <div className="results-header">
        <h2>Transform Results</h2>
        <span className="row-count">{data.rows.length} row(s)</span>
      </div>
      <div className="table-wrapper">
        <table className="results-table">
          <thead>
            <tr>
              {data.columns.map((col) => (
                <th key={col}>{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.rows.map((row, i) => (
              <tr key={i}>
                {data.columns.map((col) => (
                  <td key={col}>{row[col] != null ? String(row[col]) : ""}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default ResultsTable;
