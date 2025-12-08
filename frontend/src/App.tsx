import { useState } from "react";

function App() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const API_BASE = import.meta.env.VITE_API_BASE;

  async function handleSubmit() {
    setLoading(true);
    setResult(null);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/url_file`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });

      if (!res.ok) {
        throw new Error(`API Error: ${res.status}`);
      }

      const data = await res.json();
      setResult(JSON.stringify(data, null, 2));
    } catch (err: any) {
      setError(err.message);
    }

    setLoading(false);
  }

  return (
    <div style={{ fontFamily: "Arial", padding: "40px", maxWidth: "600px" }}>
      <h1>Model Evaluation Dashboard</h1>

      <p>Enter a file URL to evaluate using your AWS backend.</p>

      <input
        type="text"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        placeholder="https://example.com/requirements.txt"
        style={{
          width: "100%",
          padding: "12px",
          marginBottom: "10px",
          borderRadius: "8px",
          border: "1px solid #666",
        }}
      />

      <button
        onClick={handleSubmit}
        disabled={loading}
        style={{
          padding: "12px 20px",
          borderRadius: "8px",
          background: loading ? "#aaa" : "#0066ff",
          color: "white",
          border: "none",
          cursor: "pointer",
        }}
      >
        {loading ? "Evaluating..." : "Submit"}
      </button>

      {error && (
        <pre
          style={{
            marginTop: "20px",
            padding: "12px",
            background: "#ffdddd",
            color: "#a00",
            borderRadius: "8px",
          }}
        >
          ❌ {error}
        </pre>
      )}

      {result && (
        <pre
          style={{
            marginTop: "20px",
            padding: "12px",
            background: "#eef",
            borderRadius: "8px",
            whiteSpace: "pre-wrap",
          }}
        >
          {result}
        </pre>
      )}
    </div>
  );
}

export default App;
