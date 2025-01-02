import React, { useState, useEffect } from "react";

const Dashboard = () => {
  const [games, setGames] = useState([]);

  useEffect(() => {
    fetch("http://localhost:8000/api/games/")
      .then((res) => res.json())
      .then((data) => setGames(data.games))
      .catch((error) => console.error("Error fetching games:", error));
  }, []);

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold text-gray-800">Dashboard</h1>
      <table className="w-full mt-4 border border-gray-300">
        <thead>
          <tr className="bg-gray-100">
            <th className="px-4 py-2">Game ID</th>
            <th className="px-4 py-2">Opponent</th>
            <th className="px-4 py-2">Result</th>
          </tr>
        </thead>
        <tbody>
          {games.map((game) => (
            <tr key={game.id}>
              <td className="px-4 py-2 border">{game.id}</td>
              <td className="px-4 py-2 border">{game.opponent}</td>
              <td className="px-4 py-2 border">{game.result}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default Dashboard;
