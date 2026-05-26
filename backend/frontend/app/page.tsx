"use client";

import { useState } from "react";
import { generateApp } from "./lib/api";

export default function Home() {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleGenerate = async () => {
    if (!prompt) return;

    setLoading(true);

    try {
      const data = await generateApp(prompt);
      setResult(data);
    } catch (error) {
      console.error(error);
      alert("Generation failed");
    }

    setLoading(false);
  };

  return (
    <main className="min-h-screen p-10 bg-gray-100">
      <div className="max-w-4xl mx-auto bg-white p-8 rounded-xl shadow">

        <h1 className="text-4xl font-bold mb-6">
          AI Compiler System
        </h1>

        <textarea
          className="w-full h-40 border rounded p-4 text-black"
          placeholder="Describe your app..."
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
        />

        <button
          onClick={handleGenerate}
          className="bg-black text-white px-6 py-3 rounded mt-4"
        >
          {loading ? "Generating..." : "Generate App"}
        </button>

        {result && (
          <pre className="mt-6 bg-gray-200 p-4 rounded overflow-auto text-sm">
            {JSON.stringify(result, null, 2)}
          </pre>
        )}
      </div>
    </main>
  );
}