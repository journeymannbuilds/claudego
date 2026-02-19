import React, { useState } from "react";
import TransformForm from "./components/TransformForm";
import ResultsTable from "./components/ResultsTable";
import "./App.css";

function App() {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (origin, destination) => {
    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const response = await fetch("/api/transform", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ origin, destination }),
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.error || "Request failed");
      }

      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>Databricks Transform</h1>
        <p>Enter origin and destination to run a data transform</p>
      </header>

      <main className="app-main">
        <TransformForm onSubmit={handleSubmit} loading={loading} />

        {loading && (
          <div className="status-message loading">
            Running transform on Databricks...
          </div>
        )}

        {error && <div className="status-message error">Error: {error}</div>}

        {results && <ResultsTable data={results} />}
      </main>
    </div>
  );
}

export default App;
