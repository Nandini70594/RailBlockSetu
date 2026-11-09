import React, { createContext, useContext, useState, useEffect } from "react";
import { User, UserRole, DepartmentType } from "../types";
import { api } from "../api/client";

interface DemoCredential {
  role: UserRole;
  title: string;
  username: string;
  password: string;
  name: string;
  department: DepartmentType;
  description: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  switchRole: (username: string) => Promise<void>;
  demoCredentials: DemoCredential[];
  isAdmin: boolean;
  isOperations: boolean;
  isDepartmentOfficer: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem("railblocksetu_token"));
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [demoCredentials, setDemoCredentials] = useState<DemoCredential[]>([]);

  useEffect(() => {
    // Load demo credentials list
    api.getDemoCredentials()
      .then((creds) => setDemoCredentials(creds))
      .catch((err) => console.error("Failed to load demo credentials", err));

    // If token exists, verify and fetch user
    if (token) {
      api.getMe()
        .then((u) => setUser(u))
        .catch(() => {
          localStorage.removeItem("railblocksetu_token");
          setToken(null);
          setUser(null);
        })
        .finally(() => setIsLoading(false));
    } else {
      // Auto-login default Operations Officer for hackathon evaluator convenience
      login("ops_officer", "ops123").finally(() => setIsLoading(false));
    }
  }, []);

  const login = async (username: string, password: string) => {
    setIsLoading(true);
    try {
      const res = await api.login(username, password);
      localStorage.setItem("railblocksetu_token", res.access_token);
      setToken(res.access_token);
      setUser(res.user);
    } catch (err) {
      console.error("Login failed:", err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const switchRole = async (username: string) => {
    const cred = demoCredentials.find((c) => c.username === username);
    if (cred) {
      await login(cred.username, cred.password);
    }
  };

  const logout = () => {
    localStorage.removeItem("railblocksetu_token");
    setToken(null);
    setUser(null);
  };

  const isAdmin = user?.role === "ADMIN";
  const isOperations = user?.role === "OPERATIONS_OFFICER" || isAdmin;
  const isDepartmentOfficer = user?.role === "DEPARTMENT_OFFICER" || isAdmin;

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        login,
        logout,
        switchRole,
        demoCredentials,
        isAdmin,
        isOperations,
        isDepartmentOfficer,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
