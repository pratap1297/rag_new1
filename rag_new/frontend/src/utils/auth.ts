export interface User {
  id: string;
  email: string;
  name: string;
  role: 'user' | 'admin';
  token: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

const AUTH_STORAGE_KEY = 'ai_force_auth_user';

export const authUtils = {
  // Store user data in localStorage
  setUser: (user: User): void => {
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(user));
  },

  // Get user data from localStorage
  getUser: (): User | null => {
    const userData = localStorage.getItem(AUTH_STORAGE_KEY);
    if (!userData) return null;
    
    try {
      return JSON.parse(userData);
    } catch (error) {
      console.error('Error parsing user data:', error);
      return null;
    }
  },

  // Remove user data from localStorage
  removeUser: (): void => {
    localStorage.removeItem(AUTH_STORAGE_KEY);
  },

  // Check if user is authenticated
  isAuthenticated: (): boolean => {
    return authUtils.getUser() !== null;
  },

  // Check if user is admin
  isAdmin: (): boolean => {
    const user = authUtils.getUser();
    return user?.role === 'admin';
  },

  // Check if user is regular user
  isUser: (): boolean => {
    const user = authUtils.getUser();
    return user?.role === 'user';
  },

  // Get user token
  getToken: (): string | null => {
    const user = authUtils.getUser();
    return user?.token || null;
  }
};

// Mock authentication service
export const authService = {
  // Mock login function
  login: async (credentials: LoginCredentials): Promise<User> => {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Mock user validation
    if (credentials.email === 'admin@example.com' && credentials.password === 'admin123') {
      const user: User = {
        id: '1',
        email: credentials.email,
        name: 'Admin User',
        role: 'admin',
        token: 'mock-admin-token-' + Date.now()
      };
      return user;
    } else if (credentials.email === 'user@example.com' && credentials.password === 'user123') {
      const user: User = {
        id: '2',
        email: credentials.email,
        name: 'Regular User',
        role: 'user',
        token: 'mock-user-token-' + Date.now()
      };
      return user;
    } else {
      throw new Error('Invalid credentials');
    }
  },

  // Mock logout function
  logout: async (): Promise<void> => {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500));
    authUtils.removeUser();
  }
}; 