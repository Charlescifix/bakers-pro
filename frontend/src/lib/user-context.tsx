import { createContext, useContext, useEffect, useState } from 'react';
import { api } from './api';

export type CurrentUser = {
  id: string;
  tenant_id: string;
  tenant_name: string;
  full_name: string;
  email: string;
  role: string;
};

const UserContext = createContext<CurrentUser | null>(null);

export function UserProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);

  useEffect(() => {
    if (!localStorage.getItem('access_token')) return;
    api.get<CurrentUser>('/auth/me').then((r) => setUser(r.data)).catch(() => {});
  }, []);

  return <UserContext.Provider value={user}>{children}</UserContext.Provider>;
}

export function useUser(): CurrentUser | null {
  return useContext(UserContext);
}
