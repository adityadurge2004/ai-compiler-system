const API_URL = process.env.NEXT_PUBLIC_API_URL;

export async function generateApp(prompt: string) {
  const response = await fetch(`${API_URL}/api/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      prompt,
      skip_repair: false,
      max_repair_iterations: 3,
    }),
  });

  const data = await response.json();

  console.log("API RESPONSE:", data);

  return data;
}