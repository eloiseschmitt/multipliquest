export type UserRole = "PARENT" | "CHILD";

export interface AuthUser {
  id: number;
  username: string;
  displayName: string;
  role: UserRole;
  currentLevel: number;
  totalXp: number;
}

export interface ApiUser {
  id: number;
  username: string;
  display_name: string;
  role: UserRole;
  current_level: number;
  total_xp: number;
}

export interface UserResponse {
  user: ApiUser;
}
