import React, { createContext, useContext, useState, useEffect } from 'react';
import { UserSummary, UserRole } from '../types';
import { api } from '../lib/api';

interface AuthContextType {
  user: UserSummary | null;
  token: string | null;
  isLoading: boolean;
  selectedAcademicYearId: number | null;
  setSelectedAcademicYearId: (id: number | null) => void;
  login: (token: string, user: UserSummary) => void;
  logout: () => void;
  switchDemoRole: (targetRole: UserRole, institutionId?: number) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserSummary | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('edutrace_token'));
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [selectedAcademicYearId, setSelectedAcademicYearId] = useState<number | null>(null);

  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('edutrace_token');
      if (storedToken) {
        try {
          const me = await api.getMe();
          setUser(me);
        } catch (e) {
          console.error('Session expired or invalid:', e);
          localStorage.removeItem('edutrace_token');
          setToken(null);
          setUser(null);
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, []);

  const login = (newToken: string, newUser: UserSummary) => {
    localStorage.setItem('edutrace_token', newToken);
    setToken(newToken);
    setUser(newUser);
  };

  const logout = () => {
    localStorage.removeItem('edutrace_token');
    setToken(null);
    setUser(null);
  };

  const switchDemoRole = async (targetRole: UserRole, institutionId?: number) => {
    setIsLoading(true);
    try {
      const res = await api.demoSwitchRole(targetRole, institutionId);
      login(res.access_token, res.user);
    } catch (e) {
      console.error('Failed to switch demo role:', e);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        selectedAcademicYearId,
        setSelectedAcademicYearId,
        login,
        logout,
        switchDemoRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
