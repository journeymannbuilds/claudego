import React, { useState } from "react";
import "./TransformForm.css";

function TransformForm({ onSubmit, loading }) {
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (origin.trim() && destination.trim()) {
      onSubmit(origin.trim(), destination.trim());
    }
  };

  return (
    <form className="transform-form" onSubmit={handleSubmit}>
      <div className="form-row">
        <div className="form-group">
          <label htmlFor="origin">Origin</label>
          <input
            id="origin"
            type="text"
            value={origin}
            onChange={(e) => setOrigin(e.target.value)}
            placeholder="e.g. SFO, us-west, table_a"
            disabled={loading}
          />
        </div>
        <div className="form-group">
          <label htmlFor="destination">Destination</label>
          <input
            id="destination"
            type="text"
            value={destination}
            onChange={(e) => setDestination(e.target.value)}
            placeholder="e.g. JFK, us-east, table_b"
            disabled={loading}
          />
        </div>
      </div>
      <button type="submit" disabled={loading || !origin.trim() || !destination.trim()}>
        {loading ? "Running..." : "Run Transform"}
      </button>
    </form>
  );
}

export default TransformForm;
