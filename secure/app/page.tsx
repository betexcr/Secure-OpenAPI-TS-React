"use client"
import { useState, useEffect } from "react";
import axios from "axios";

export default function Home() {
  const [token, setToken] = useState("");
  const [items, setItems] = useState([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  useEffect(() => {
    if (token) {
      fetchItems();
    }
  }, [token]);

  const login = async () => {
    try {
      const res = await axios.post("http://localhost:8000/token", {
        username: "admin",
        password: "password",
      }, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" }
      });
      setToken(res.data.access_token);
    } catch (error) {
      console.error("Login failed:", error.response ? error.response.data : error);
    }
  };

  const fetchItems = async () => {
    try {
      const res = await axios.get("http://localhost:8000/items/", {
        headers: { Authorization: `Bearer ${token}` },
      });
      setItems(res.data);
    } catch (error) {
      console.error("Error fetching items:", error.response ? error.response.data : error);
    }
  };

  const createItem = async () => {
    try {
      await axios.post("http://localhost:8000/items/", { name, description }, {
        headers: { Authorization: `Bearer ${token}` },
      });
      fetchItems();
    } catch (error) {
      console.error("Error creating item:", error.response ? error.response.data : error);
    }
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold">FastAPI + Next.js Secure CRUD</h1>
      <button onClick={login} className="bg-blue-500 text-white px-4 py-2 rounded">
        Login
      </button>
      <button onClick={fetchItems} className="ml-2 bg-green-500 text-white px-4 py-2 rounded">
        Fetch Items
      </button>
      <div className="mt-4">
        <input
          className="border p-2 mr-2"
          placeholder="Item Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <input
          className="border p-2 mr-2"
          placeholder="Description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
        <button onClick={createItem} className="bg-purple-500 text-white px-4 py-2 rounded">
          Create Item
        </button>
      </div>
      <ul className="mt-4">
        {items.map((item) => (
          <li key={item.id} className="border p-2 mb-2">
            {item.name}: {item.description}
          </li>
        ))}
      </ul>
    </div>
  );
}
