import { createContext, useContext, useEffect, useState } from "react";
import { api } from "./api";

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => {
    const t = new URLSearchParams(window.location.search).get("token");
    if (t) {
      localStorage.setItem("token", t);
      window.history.replaceState({}, "", window.location.pathname);
    }
    return localStorage.getItem("token");
  });
  const [username, setUsername] = useState(null);
  const [modal, setModal] = useState(null); // null | "login" | "signup"


  // 2. Whenever we have a token, load the real user from the backend
  useEffect(() => {
    if (!token) {
      setUsername(null);
      return;
    }
    api("/auth/me")
      .then((me) => setUsername(me.username))
      .catch(() => logout()); // expired or invalid token
  }, [token]);

  function saveToken(data) {
    localStorage.setItem("token", data.access_token);
    setToken(data.access_token);
    setModal(null);
  }

  async function login(email, password) {
    saveToken(await api("/auth/login", { email, password }));
  }

  async function register(username, email, password) {
    saveToken(await api("/auth/register", { username, email, password }));
  }

  function logout() {
    localStorage.removeItem("token");
    setToken(null);
    setUsername(null);
  }

  return (
    <AuthContext.Provider
      value={{
        isLoggedIn: !!token,
        username,
        login,
        register,
        logout,
        modal,
        openAuth: setModal,
        closeAuth: () => setModal(null),
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}