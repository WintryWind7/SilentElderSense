<template>
  <div class="platform-dashboard">
    <!-- 标签页 -->
    <div class="tab-bar">
      <button class="tab-btn" :class="{ active: activeTab === 'overview' }" @click="activeTab = 'overview'">数据概览</button>
      <button class="tab-btn" :class="{ active: activeTab === 'users' }" @click="activeTab = 'users'">用户管理</button>
    </div>

    <!-- 隐私声明 -->
    <div class="privacy-notice" v-if="activeTab === 'overview'">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 2L2 7l10 5 10-5-10-5z"/>
        <path d="M2 17l10 5 10-5"/>
        <path d="M2 12l10 5 10-5"/>
      </svg>
      <span>平台统计数据已采用差分隐私技术处理，数值与原始数据可能存在轻微差异，但不影响总体趋势判断。</span>
    </div>

    <!-- 数据概览 -->
    <template v-if="activeTab === 'overview'">
      <!-- 组织信息 -->
      <section class="org-section" v-if="orgInfo">
        <div class="org-card">
          <div class="org-header">
            <h3>{{ orgInfo.name }}</h3>
            <span class="org-status" :class="orgInfo.status">{{ orgInfo.status === 'active' ? '运营中' : '已停用' }}</span>
          </div>
          <p class="org-desc">{{ orgInfo.description || '暂无描述' }}</p>
          <div class="org-meta">
            <span>社区组: {{ communities.length }} 个</span>
            <span>覆盖用户: {{ stats.member_count || 0 }} 人</span>
          </div>
        </div>
      </section>

      <!-- 统计卡片 -->
      <section class="stats-section">
        <div class="stats-grid">
          <div class="stat-card" v-for="card in statsCards" :key="card.key">
            <div class="stat-icon" :class="card.type">
              <span>{{ card.icon }}</span>
            </div>
            <div class="stat-content">
              <span class="stat-value">{{ card.value }}</span>
              <span class="stat-label">{{ card.label }}</span>
            </div>
            <div class="stat-trend" v-if="card.trend" :class="card.trend > 0 ? 'up' : 'down'">
              <span>{{ Math.abs(card.trend) }}%</span>
            </div>
          </div>
        </div>
      </section>

      <!-- 图表 -->
      <section class="charts-section">
        <div class="charts-grid">
          <div class="chart-card">
            <div class="card-header">
              <h3 class="card-title">事件类型分布</h3>
            </div>
            <div class="card-body">
              <div ref="typeChartRef" class="chart-container"></div>
            </div>
          </div>
          <div class="chart-card">
            <div class="card-header">
              <h3 class="card-title">风险等级分布</h3>
            </div>
            <div class="card-body">
              <div ref="riskChartRef" class="chart-container"></div>
            </div>
          </div>
        </div>
      </section>

      <!-- 每日趋势 -->
      <section class="trend-section">
        <div class="chart-card">
          <div class="card-header">
            <h3 class="card-title">每日事件趋势</h3>
            <div class="filter-group">
              <select v-model="trendDays" @change="loadDailyTrend" class="filter-select">
                <option :value="7">近 7 天</option>
                <option :value="14">近 14 天</option>
                <option :value="30">近 30 天</option>
              </select>
            </div>
          </div>
          <div class="card-body">
            <div ref="trendChartRef" class="chart-container"></div>
          </div>
        </div>
      </section>

      <!-- 社区组列表 -->
      <section class="communities-section">
        <div class="chart-card">
          <div class="card-header">
            <h3 class="card-title">社区组概览</h3>
          </div>
          <div class="card-body">
            <div class="table-wrapper">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>社区组名称</th>
                    <th>地址</th>
                    <th>覆盖用户</th>
                    <th>状态</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="c in communities" :key="c.id" class="table-row">
                    <td>{{ c.name }}</td>
                    <td>{{ c.address || '-' }}</td>
                    <td>{{ c.member_count }} 人</td>
                    <td>
                      <span class="status-badge" :class="c.status === 'active' ? 'confirmed' : 'pending'">
                        <span class="status-dot"></span>
                        {{ c.status === 'active' ? '运营中' : '已停用' }}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
              <div v-if="communities.length === 0" class="empty-state">
                <p>暂无社区组数据</p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </template>

    <!-- 用户管理 -->
    <template v-if="activeTab === 'users'">
      <section class="users-section">
        <div class="section-header">
          <h3>用户管理</h3>
          <button class="btn-primary" @click="showCreateUser = true">创建用户</button>
        </div>
        <div class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>用户名</th>
                <th>邮箱</th>
                <th>社区组</th>
                <th>创建时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="u in myUsers" :key="u.id">
                <td>{{ u.username }}</td>
                <td>{{ u.email || '-' }}</td>
                <td>{{ u.community_group_name || '-' }}</td>
                <td>{{ formatDate(u.created_at) }}</td>
                <td>
                  <div class="action-btns">
                    <button class="action-btn secondary" @click="editMyUser(u)">编辑</button>
                    <button class="action-btn danger" @click="handleResetPassword(u)">重设密码</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-if="myUsers.length === 0" class="empty-state">暂无用户</div>
        </div>
      </section>
    </template>

    <!-- 创建/编辑用户弹窗 -->
    <div v-if="showCreateUser" class="modal-overlay" @click.self="showCreateUser = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ editingUser ? '编辑用户' : '创建用户' }}</h3>
          <button class="modal-close" @click="showCreateUser = false; editingUser = null">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-item" v-if="!editingUser">
            <label>用户名</label>
            <input v-model="newUser.username" placeholder="输入用户名" class="form-input" />
          </div>
          <div class="form-item" v-if="!editingUser">
            <label>密码</label>
            <input v-model="newUser.password" type="password" placeholder="输入密码" class="form-input" />
          </div>
          <div class="form-item">
            <label>邮箱（可选）</label>
            <input v-model="newUser.email" placeholder="输入邮箱" class="form-input" />
          </div>
          <div class="form-item">
            <label>社区组（可选）</label>
            <select v-model="newUser.community_group_id" class="form-input">
              <option :value="null">无</option>
              <option v-for="g in communities" :key="g.id" :value="g.id">{{ g.name }}</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showCreateUser = false; editingUser = null">取消</button>
          <button class="btn-primary" @click="saveUser" :disabled="!editingUser && (!newUser.username || !newUser.password)">
            {{ editingUser ? '保存' : '创建' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 重设密码弹窗 -->
    <div v-if="showResetPassword" class="modal-overlay" @click.self="showResetPassword = false">
      <div class="modal-content" style="width: 360px">
        <div class="modal-header">
          <h3>重设密码</h3>
          <button class="modal-close" @click="showResetPassword = false">✕</button>
        </div>
        <div class="modal-body">
          <p class="reset-user-info">用户：{{ resetTarget?.username }}</p>
          <div class="form-item">
            <label>新密码</label>
            <input v-model="newPassword" type="password" placeholder="输入新密码" class="form-input" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showResetPassword = false">取消</button>
          <button class="btn-primary" @click="confirmResetPassword" :disabled="!newPassword || newPassword.length < 4">确认重设</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import {
  getMyProfile, getMyCommunities, getPlatformStats, getPlatformDailyTrend,
  getMyUsers, createMyUser, updateMyUser, resetMyUserPassword,
} from '@/api/platform'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'

const activeTab = ref('overview')

const orgInfo = ref(null)
const communities = ref([])
const stats = ref({ total: 0, by_type: {}, by_risk: {}, by_status: {}, trends: {}, member_count: 0 })
const trendDays = ref(7)

const typeChartRef = ref(null)
const riskChartRef = ref(null)
const trendChartRef = ref(null)

// 用户管理
const myUsers = ref([])
const showCreateUser = ref(false)
const editingUser = ref(null)
const newUser = ref({ username: '', password: '', email: '', community_group_id: null })

// 重设密码
const showResetPassword = ref(false)
const resetTarget = ref(null)
const newPassword = ref('')

const typeLabels = { FALLEN: '跌倒检测', STILLNESS: '长时间静止', NIGHT_ABNORMAL: '夜间异常' }
const riskLabels = { HIGH: '高风险', MEDIUM: '中风险', LOW: '低风险' }
const riskColors = { HIGH: '#ef4444', MEDIUM: '#f59e0b', LOW: '#22c55e' }

const statsCards = computed(() => {
  const s = stats.value
  const t = s.trends || {}
  return [
    { key: 'total', label: '事件总数', value: s.display?.total ?? s.total, type: 'primary', icon: '📊', trend: t.total },
    { key: 'high', label: '高风险', value: s.display?.by_risk?.HIGH ?? s.by_risk?.HIGH ?? 0, type: 'danger', icon: '🔴' },
    { key: 'medium', label: '中风险', value: s.display?.by_risk?.MEDIUM ?? s.by_risk?.MEDIUM ?? 0, type: 'warning', icon: '🟡' },
    { key: 'members', label: '覆盖用户', value: s.member_count || 0, type: 'info', icon: '👥' },
  ]
})

async function loadOrg() {
  try {
    const res = await getMyProfile()
    orgInfo.value = {
      name: res.org_name || res.username,
      description: res.org_description,
      status: 'active',
    }
  } catch (e) { console.error(e) }
}

async function loadCommunities() {
  try {
    const res = await getMyCommunities()
    communities.value = Array.isArray(res.data) ? res.data : res
  } catch (e) { console.error(e) }
}

async function loadStats() {
  try {
    stats.value = await getPlatformStats()
    await nextTick()
    renderCharts()
  } catch (e) { console.error(e) }
}

async function loadDailyTrend() {
  try {
    const res = await getPlatformDailyTrend(trendDays.value)
    renderTrendChart(res)
  } catch (e) { console.error(e) }
}

function renderCharts() {
  const s = stats.value
  // 事件类型饼图
  if (typeChartRef.value) {
    const chart = echarts.init(typeChartRef.value)
    const typeData = Object.entries(s.by_type || {}).map(([k, v]) => ({
      name: typeLabels[k] || k, value: s.display?.by_type?.[k] ?? v
    }))
    chart.setOption({
      tooltip: { trigger: 'item' },
      series: [{
        type: 'pie', radius: ['40%', '70%'],
        data: typeData.length ? typeData : [{ name: '暂无数据', value: 0 }],
        label: { color: '#aaa' },
        itemStyle: { borderColor: '#1a1a24', borderWidth: 2 },
      }]
    })
  }
  // 风险等级柱状图
  if (riskChartRef.value) {
    const chart = echarts.init(riskChartRef.value)
    const categories = Object.keys(riskLabels)
    const values = categories.map(k => s.display?.by_risk?.[k] ?? s.by_risk?.[k] ?? 0)
    chart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: categories.map(k => riskLabels[k]), axisLabel: { color: '#aaa' } },
      yAxis: { type: 'value', axisLabel: { color: '#aaa' }, splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } } },
      series: [{
        type: 'bar', data: categories.map((k, i) => ({ value: values[i], itemStyle: { color: riskColors[k] } })),
        barWidth: 40,
      }]
    })
  }
}

function renderTrendChart(data) {
  if (!trendChartRef.value || !data) return
  const chart = echarts.init(trendChartRef.value)
  const types = data.by_type || {}
  const series = Object.entries(types).map(([type, values]) => ({
    name: typeLabels[type] || type,
    type: 'line',
    smooth: true,
    data: values,
    lineStyle: { width: 2 },
  }))
  chart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { textStyle: { color: '#aaa' }, top: 0 },
    grid: { top: 40, left: 50, right: 20, bottom: 30 },
    xAxis: { type: 'category', data: data.dates || [], axisLabel: { color: '#aaa' } },
    yAxis: { type: 'value', axisLabel: { color: '#aaa' }, splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } } },
    series,
  })
}

// 用户管理
async function loadMyUsers() {
  try {
    const res = await getMyUsers()
    myUsers.value = Array.isArray(res.data) ? res.data : res
  } catch (e) { console.error(e) }
}

function editMyUser(u) {
  editingUser.value = u
  newUser.value = {
    username: u.username,
    email: u.email || '',
    community_group_id: u.community_group_id,
  }
  showCreateUser.value = true
}

async function saveUser() {
  try {
    if (editingUser.value) {
      await updateMyUser(editingUser.value.id, {
        email: newUser.value.email,
        community_group_id: newUser.value.community_group_id,
      })
      ElMessage.success('更新成功')
    } else {
      await createMyUser(newUser.value)
      ElMessage.success('用户创建成功')
    }
    showCreateUser.value = false
    editingUser.value = null
    newUser.value = { username: '', password: '', email: '', community_group_id: null }
    loadMyUsers()
    loadStats()
  } catch (e) {
    ElMessage.error(e.response?.data?.error || '操作失败')
  }
}

function handleResetPassword(u) {
  resetTarget.value = u
  newPassword.value = ''
  showResetPassword.value = true
}

async function confirmResetPassword() {
  try {
    await resetMyUserPassword(resetTarget.value.id, { new_password: newPassword.value })
    ElMessage.success(`${resetTarget.value.username} 密码已重置`)
    showResetPassword.value = false
  } catch (e) {
    ElMessage.error(e.response?.data?.error || '重设失败')
  }
}

function formatDate(iso) {
  if (!iso) return '-'
  return new Date(iso).toLocaleDateString('zh-CN')
}

onMounted(() => {
  loadOrg()
  loadCommunities()
  loadStats()
  loadDailyTrend()
  loadMyUsers()
})
</script>

<style scoped>
.platform-dashboard {
  max-width: 1200px;
  margin: 0 auto;
}

.privacy-notice {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 20px;
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 12px;
  color: #93c5fd;
  font-size: 13px;
  margin-bottom: 24px;
}

.privacy-notice svg {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.org-section { margin-bottom: 24px; }

.org-card {
  padding: 20px 24px;
  background: rgba(26, 26, 36, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 16px;
}

.org-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.org-header h3 {
  font-size: 18px;
  font-weight: 700;
  color: #f0f0f5;
  margin: 0;
}

.org-status {
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 600;
}

.org-status.active { background: rgba(34, 197, 94, 0.15); color: #4ade80; }
.org-status.suspended { background: rgba(239, 68, 68, 0.15); color: #f87171; }

.org-desc { color: #888; font-size: 14px; margin: 4px 0 12px; }

.org-meta {
  display: flex;
  gap: 24px;
  color: #aaa;
  font-size: 13px;
}

.stats-section { margin-bottom: 24px; }

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-card {
  padding: 20px;
  background: rgba(26, 26, 36, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.stat-icon.primary { background: rgba(249, 115, 22, 0.15); }
.stat-icon.danger { background: rgba(239, 68, 68, 0.15); }
.stat-icon.warning { background: rgba(245, 158, 11, 0.15); }
.stat-icon.info { background: rgba(59, 130, 246, 0.15); }

.stat-content { display: flex; flex-direction: column; }
.stat-value { font-size: 24px; font-weight: 700; color: #f0f0f5; }
.stat-label { font-size: 13px; color: #888; }

.stat-trend {
  margin-left: auto;
  font-size: 13px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 8px;
}
.stat-trend.up { color: #f87171; background: rgba(239, 68, 68, 0.1); }
.stat-trend.down { color: #4ade80; background: rgba(34, 197, 94, 0.1); }

.charts-section { margin-bottom: 24px; }

.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.chart-card {
  background: rgba(26, 26, 36, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  overflow: hidden;
}

.card-header {
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #f0f0f5;
  margin: 0;
}

.card-body { padding: 16px; }

.chart-container { height: 280px; }

.filter-group { display: flex; gap: 8px; }

.filter-select {
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: #ccc;
  font-size: 13px;
  outline: none;
}

.trend-section { margin-bottom: 24px; }

.communities-section { margin-bottom: 24px; }

.table-wrapper { overflow-x: auto; }

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  text-align: left;
  padding: 12px 16px;
  font-size: 12px;
  color: #888;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.data-table td {
  padding: 12px 16px;
  font-size: 14px;
  color: #ddd;
  border-bottom: 1px solid rgba(255, 255, 255, 0.03);
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 10px;
  border-radius: 10px;
  font-size: 12px;
}

.status-badge.confirmed { background: rgba(34, 197, 94, 0.15); color: #4ade80; }
.status-badge.pending { background: rgba(245, 158, 11, 0.15); color: #fbbf24; }

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #666;
}

@media (max-width: 768px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .charts-grid { grid-template-columns: 1fr; }
}

/* 标签页 */
.tab-bar {
  display: flex;
  gap: 4px;
  margin-bottom: 24px;
  background: rgba(26, 26, 36, 0.6);
  border-radius: 12px;
  padding: 4px;
}

.tab-btn {
  flex: 1;
  padding: 10px;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: #888;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn.active {
  background: linear-gradient(135deg, #f97316, #ea580c);
  color: white;
}

.tab-btn:hover:not(.active) {
  color: #ccc;
  background: rgba(255, 255, 255, 0.05);
}

/* 用户管理 */
.users-section {
  background: rgba(26, 26, 36, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  padding: 20px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.section-header h3 {
  color: #f0f0f5;
  font-size: 16px;
  margin: 0;
}

.btn-primary {
  padding: 8px 20px;
  background: linear-gradient(135deg, #f97316, #ea580c);
  border: none;
  border-radius: 10px;
  color: white;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  padding: 8px 20px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  color: #ccc;
  font-size: 14px;
  cursor: pointer;
}

.action-btns { display: flex; gap: 6px; }

.action-btn {
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  border: none;
}

.action-btn.secondary {
  background: rgba(255, 255, 255, 0.05);
  color: #aaa;
}

.action-btn.danger {
  background: rgba(239, 68, 68, 0.1);
  color: #f87171;
}

/* 弹窗 */
.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal-content {
  background: #1e1e2e;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  width: 480px;
  max-width: 90vw;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.modal-header h3 {
  color: #f0f0f5;
  margin: 0;
}

.modal-close {
  background: none;
  border: none;
  color: #888;
  font-size: 18px;
  cursor: pointer;
}

.modal-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.modal-footer {
  padding: 16px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-item label {
  font-size: 13px;
  color: #888;
}

.form-input {
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: #ddd;
  font-size: 14px;
  outline: none;
}

.form-input:focus {
  border-color: rgba(249, 115, 22, 0.5);
}

.reset-user-info {
  color: #ddd;
  font-size: 14px;
  margin: 0 0 12px;
}
</style>
