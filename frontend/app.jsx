import React, { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const [darkMode, setDarkMode] = useState(true);
  const socket = useRef(null);
  const bottomRef = useRef(null);

  // System preference detection on first load
  useEffect(() => {
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    setDarkMode(prefersDark);
  }, []);

  // WebSocket connection
  const connectSocket = () => {
    socket.current = new WebSocket("ws://localhost:8000/ws");

    socket.current.onmessage = (event) => {
      const text = event.data.trim();
      setMessages((prev) => [...prev, { text, sender: "bot" }]);
      setTyping(false);
    };

    socket.current.onerror = (err) => {
      console.error("WebSocket error:", err);
    };
  };

  useEffect(() => {
    connectSocket();
    return () => socket.current?.close();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, typing]);

  const sendMessage = () => {
    if (!input.trim()) return;
    socket.current.send(input);
    setMessages((prev) => [...prev, { text: input, sender: "user" }]);
    setInput("");
    setTyping(true);
  };

  const resetChat = () => {
    socket.current?.close();
    setMessages([]);
    setInput("");
    setTyping(false);
    connectSocket();
  };

  const isPasswordPrompt =
    messages.length > 0 &&
    messages[messages.length - 1].text.toLowerCase().includes("password");

  return (
    <div className={`${darkMode ? "bg-gray-900 text-white" : "bg-white text-black"} min-h-screen flex flex-col p-4 transition-colors duration-300`}>
      {/* Header */}
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-xl font-bold text-center flex-1">✈️ AI Travel Assistant</h1>
        <div className="flex gap-2">
          <button
            onClick={resetChat}
            className="bg-red-500 text-white px-3 py-1 rounded hover:bg-red-600"
          >
            Reset
          </button>
          <button
            onClick={() => setDarkMode(!darkMode)}
            className="bg-gray-700 text-white px-3 py-1 rounded hover:bg-gray-600"
          >
            {darkMode ? "🌞 Light" : "🌙 Dark"}
          </button>
        </div>
      </div>

      {/* Chat Window */}
      <div className="flex-1 overflow-y-auto space-y-2 max-w-2xl mx-auto w-full">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`max-w-[80%] p-3 rounded-lg whitespace-pre-wrap ${
              msg.sender === "user"
                ? "bg-blue-600 ml-auto"
                : darkMode
                ? "bg-gray-700 mr-auto"
                : "bg-gray-200 mr-auto text-black"
            }`}
          >
            <ReactMarkdown>{msg.text}</ReactMarkdown>
          </div>
        ))}

        {typing && (
          <div
            className={`max-w-[80%] p-3 rounded-lg mr-auto animate-pulse ${
              darkMode ? "bg-gray-700" : "bg-gray-200 text-black"
            }`}
          >
            <span className="text-gray-300">Typing...</span>
          </div>
        )}
        <div ref={bottomRef}></div>
      </div>

      {/* Input Area */}
      <div className="mt-4 flex max-w-2xl mx-auto w-full relative">
        <input
          type={isPasswordPrompt ? "password" : "text"}
          className={`flex-1 p-3 rounded-l-lg outline-none ${
            darkMode ? "bg-gray-800 text-white" : "bg-gray-100 text-black"
          }`}
          placeholder="Type your message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
        />
        <button
          onClick={sendMessage}
          className="bg-blue-600 px-5 rounded-r-lg hover:bg-blue-700"
        >
          Send
        </button>

        {/* Loading Spinner */}
        {typing && (
          <div className="absolute right-16 top-3 animate-spin rounded-full h-5 w-5 border-t-2 border-white border-opacity-50"></div>
        )}
      </div>
    </div>
  );
}
