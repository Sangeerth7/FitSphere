export const saveTokens = (data) => {
  localStorage.setItem("access", data.access);
  localStorage.setItem("refresh", data.refresh);
  localStorage.setItem("role", data.role);
  localStorage.setItem("username", data.username);
};

export const logout = () => {
  ["access", "refresh", "role", "username"].forEach((key) => localStorage.removeItem(key));
};

export const isAuthenticated = () => {
  return !!localStorage.getItem("access");
};

export const getRole = () => localStorage.getItem("role") || "member";
export const getUsername = () => localStorage.getItem("username") || "User";