export async function askOrca(message, conversationId, location = null) {
  const response = await fetch("http://127.0.0.1:8000/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      conversation_id: conversationId,
      location
    })
  });

  if (!response.ok) {
    throw new Error(await response.text());
  }

  return response.json();
}

// Example:
// const result = await askOrca(
//   "What are the current sea conditions near Visakhapatnam?",
//   "demo-session"
// );
// console.log(result.answer.summary);
// console.log(result.ocean);
// console.log(result.sources);
