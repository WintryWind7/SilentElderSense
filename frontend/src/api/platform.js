import api from './index'

// ── 管理员：平台用户 ──

export const listPlatformUsers = () => api.get('/platform/users')
export const updatePlatformUser = (userId, data) => api.put(`/platform/users/${userId}`, data)
export const listAllUsers = () => api.get('/users')
export const adminResetPassword = (data) => api.post('/admin/reset-password', data)

// ── 管理员：用户管理 ──

export const adminCreateUser = (data) => api.post('/admin/users', data)
export const adminUpdateUser = (userId, data) => api.put(`/admin/users/${userId}`, data)

// ── 管理员：社区组 ──

export const createGroup = (platformUserId, data) => api.post(`/platform/users/${platformUserId}/groups`, data)
export const listGroups = (platformUserId) => api.get(`/platform/users/${platformUserId}/groups`)
export const updateGroup = (groupId, data) => api.put(`/platform/groups/${groupId}`, data)
export const suspendGroup = (groupId) => api.delete(`/platform/groups/${groupId}`)

// ── 平台用户 ──

export const getMyProfile = () => api.get('/platform/profile')
export const getMyCommunities = () => api.get('/platform/communities')
export const getPlatformStats = (days = 7) => api.get('/platform/stats', { params: { days } })
export const getPlatformDailyTrend = (days = 7) => api.get('/platform/stats/daily', { params: { days } })

// ── 平台用户：下属用户管理 ──

export const getMyUsers = () => api.get('/platform/my-users')
export const createMyUser = (data) => api.post('/platform/my-users', data)
export const updateMyUser = (userId, data) => api.put(`/platform/my-users/${userId}`, data)
export const resetMyUserPassword = (userId, data) => api.post(`/platform/my-users/${userId}/reset-password`, data)

// ── 普通用户：社区组选择 ──

export const getAvailableGroups = (search = '') => api.get('/community/groups', { params: { search } })
export const getUserCommunity = () => api.get('/user/community')
export const setUserCommunity = (communityGroupId) => api.put('/user/community', { community_group_id: communityGroupId })
