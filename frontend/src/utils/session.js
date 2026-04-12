export function getStoredUser() {
  const rawUser = localStorage.getItem('sentinelai_user')
  if (!rawUser) return null

  try {
    return JSON.parse(rawUser)
  } catch {
    return null
  }
}

export function isPrivilegedRole(user) {
  return ['admin', 'analyst'].includes(user?.role)
}
