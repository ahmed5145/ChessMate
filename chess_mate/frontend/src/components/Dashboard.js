import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

const Dashboard = () => {
  const [games, setGames] = useState([]);
  const [message, setMessage] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    const fetchUserGames = async () => {
      const tokens = JSON.parse(localStorage.getItem("tokens"));
      if (!tokens) {
        navigate("/"); // Redirect to login if no tokens
        return;
      }
      try {
        const response = await axios.get("http://127.0.0.1:8000/api/dashboard/", {
          headers: { Authorization: `Bearer ${tokens.access}` },
        });
        setGames(response.data.games);
      } catch (error) {
        if (error.response?.status === 401) {
          localStorage.removeItem("tokens");
          navigate("/"); // Redirect to login on unauthorized
        } else {
          setMessage("Failed to load games.");
        }
      }
    };
    fetchUserGames();
  }, [navigate]);

  return (
    <div>
      <h2>Your Games</h2>
      {message && <p>{message}</p>}
      <ul>
        {games.map((game) => (
          <li key={game.id}>
            {game.title} - {game.result} ({new Date(game.played_at).toLocaleDateString()})
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Dashboard;
