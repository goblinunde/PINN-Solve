<template>
  <div class="database-view page-shell">
    <section class="page-hero">
      <div class="page-header">
        <div>
          <span class="section-kicker">{{ t('nav.database') }}</span>
          <h2 class="page-title">SQL / SSH 数据库工作台</h2>
          <p class="page-subtitle">
            在前端直接管理本地 MySQL 或经 SSH 跳转到云端 SQL 服务，完成连接、建库、建表、录入训练/测试数据和 CSV 导入。
          </p>
        </div>
        <button class="ghost-btn" @click="refreshProfiles">刷新连接</button>
      </div>

      <div class="metric-strip">
        <div class="metric-tile">
          <span class="metric-tile-label">连接配置</span>
          <strong class="metric-tile-value">{{ profiles.length }}</strong>
        </div>
        <div class="metric-tile">
          <span class="metric-tile-label">数据库数量</span>
          <strong class="metric-tile-value">{{ databaseCount }}</strong>
        </div>
        <div class="metric-tile">
          <span class="metric-tile-label">表数量</span>
          <strong class="metric-tile-value">{{ tableCount }}</strong>
        </div>
        <div class="metric-tile">
          <span class="metric-tile-label">当前连接</span>
          <strong class="metric-tile-value">{{ selectedProfile?.name || '--' }}</strong>
        </div>
      </div>
    </section>

    <div v-if="errorMessage" class="error-box">{{ errorMessage }}</div>
    <div v-if="successMessage" class="note-box">{{ successMessage }}</div>

    <div class="workspace-grid">
      <section class="surface-card login-card">
        <div class="section-header">
          <div>
            <h3>数据库登录</h3>
            <p class="section-caption">按数据库客户端的方式先建立连接，再进入库表管理与数据导入。</p>
          </div>
        </div>

        <div class="mode-switch">
          <button
            class="mode-card"
            :class="{ active: !profileForm.ssh_enabled }"
            @click="profileForm.ssh_enabled = false"
          >
            <span class="mode-icon">◎</span>
            <span class="mode-title">Navicat</span>
          </button>
          <span class="mode-divider"></span>
          <button
            class="mode-card"
            :class="{ active: true }"
            disabled
          >
            <span class="mode-icon">▤</span>
            <span class="mode-title">Database</span>
          </button>
        </div>

        <div class="login-form">
          <div class="form-row">
            <label>Connection Name:</label>
            <input v-model="profileForm.name" class="tech-input" placeholder="" />
          </div>

          <div class="form-row">
            <label>Host:</label>
            <input v-model="profileForm.host" class="tech-input" placeholder="localhost" />
          </div>

          <div class="form-row split-row">
            <label>Port:</label>
            <input v-model.number="profileForm.port" type="number" class="tech-input narrow-input" />
          </div>

          <div class="form-row">
            <label>User Name:</label>
            <input v-model="profileForm.username" class="tech-input" placeholder="root" />
          </div>

          <div class="form-row">
            <label>Password:</label>
            <input v-model="profileForm.password" type="password" class="tech-input" />
          </div>

          <label class="save-secret">
            <input v-model="profileForm.save_password" type="checkbox" />
            <span>Save password</span>
          </label>

          <div class="form-row">
            <label>Database:</label>
            <input v-model="profileForm.default_database" class="tech-input" placeholder="PINNSOLVER" />
          </div>

          <label class="ssh-toggle">
            <input v-model="profileForm.ssh_enabled" type="checkbox" />
            <span>Use SSH tunnel for cloud SQL service</span>
          </label>

          <div v-if="profileForm.ssh_enabled" class="ssh-panel">
            <div class="form-row">
              <label>SSH Host:</label>
              <input v-model="profileForm.ssh_host" class="tech-input" placeholder="cloud.example.com" />
            </div>
            <div class="form-row split-row">
              <label>SSH Port:</label>
              <input v-model.number="profileForm.ssh_port" type="number" class="tech-input narrow-input" />
            </div>
            <div class="form-row">
              <label>SSH User:</label>
              <input v-model="profileForm.ssh_username" class="tech-input" />
            </div>
            <div class="form-row">
              <label>SSH Password:</label>
              <input v-model="profileForm.ssh_password" type="password" class="tech-input" />
            </div>
            <div class="form-row">
              <label>SSH Key Path:</label>
              <input v-model="profileForm.ssh_pkey_path" class="tech-input" placeholder="~/.ssh/id_rsa" />
            </div>
          </div>
        </div>

        <div class="actions">
          <button class="action-btn primary" @click="submitProfile">保存连接</button>
        </div>
      </section>

      <section class="surface-card">
        <div class="section-header">
          <div>
            <h3>已保存连接</h3>
            <p class="section-caption">选择连接后即可浏览库表、创建结构和导入数据。</p>
          </div>
        </div>

        <div v-if="profiles.length === 0" class="empty-state">当前还没有数据库连接配置。</div>
        <div v-else class="profile-list">
          <button
            v-for="profile in profiles"
            :key="profile.profile_id"
            class="profile-card"
            :class="{ active: selectedProfile?.profile_id === profile.profile_id }"
            @click="selectProfile(profile)"
          >
            <strong>{{ profile.name }}</strong>
            <span>{{ profile.username }}@{{ profile.host }}:{{ profile.port }}</span>
            <span>{{ profile.ssh_enabled ? 'SSH 隧道' : '直连' }}</span>
          </button>
        </div>

        <div v-if="selectedProfile" class="actions">
          <button class="action-btn secondary" @click="runConnectionTest">测试连接</button>
          <button class="action-btn secondary" @click="loadSchema">读取库表</button>
        </div>
      </section>
    </div>

    <div v-if="selectedProfile" class="workspace-grid">
      <section class="surface-card">
        <div class="section-header">
          <div>
            <h3>库表浏览</h3>
            <p class="section-caption">点击表名加载预览数据。当前支持 MySQL schema 作为数据库名称展示。</p>
          </div>
        </div>

        <div class="form-grid">
          <div class="form-section">
            <label>创建数据库</label>
            <input v-model="createDatabaseForm.database_name" class="tech-input" placeholder="PINNSOLVER" />
          </div>
          <div class="form-section form-end">
            <button class="action-btn primary" @click="submitCreateDatabase">创建数据库</button>
          </div>
        </div>

        <div v-if="schema.databases.length === 0" class="empty-state">当前连接还没有读取到数据库。</div>
        <div v-else class="database-list">
          <article v-for="database in schema.databases" :key="database.database" class="database-card">
            <div class="database-head">
              <strong>{{ database.database }}</strong>
              <span>{{ database.tables.length }} 张表</span>
            </div>
            <div class="table-chip-row">
              <button
                v-for="table in database.tables"
                :key="table"
                class="table-chip"
                @click="openTable(database.database, table)"
              >
                {{ table }}
              </button>
            </div>
          </article>
        </div>
      </section>

      <section class="surface-card">
        <div class="section-header">
          <div>
            <h3>建表与录入</h3>
            <p class="section-caption">先定义字段，再插入训练/测试数据，或直接用 CSV 导入。</p>
          </div>
        </div>

        <div class="form-grid">
          <div class="form-section">
            <label>目标数据库</label>
            <input v-model="tableForm.database_name" class="tech-input" placeholder="PINNSOLVER" />
          </div>
          <div class="form-section">
            <label>表名</label>
            <input v-model="tableForm.table_name" class="tech-input" placeholder="training_samples" />
          </div>
        </div>

        <div class="column-builder">
          <article v-for="(column, index) in tableForm.columns" :key="index" class="column-row">
            <input v-model="column.name" class="tech-input" placeholder="列名" />
            <input v-model="column.type" class="tech-input" placeholder="VARCHAR(255)" />
            <label class="mini-toggle">
              <span>主键</span>
              <input v-model="column.primary_key" type="checkbox" />
            </label>
            <label class="mini-toggle">
              <span>可空</span>
              <input v-model="column.nullable" type="checkbox" />
            </label>
          </article>
        </div>

        <div class="actions">
          <button class="action-btn secondary" @click="addColumn">添加字段</button>
          <button class="action-btn primary" @click="submitCreateTable">创建表</button>
        </div>

        <div class="editor-grid">
          <div class="editor-card">
            <div class="section-header compact">
              <div>
                <h3>JSON 行数据</h3>
                <p class="section-caption">适合直接填写训练/测试样本。</p>
              </div>
            </div>
            <textarea
              v-model="rowEditor"
              class="tech-textarea"
              placeholder='[{"split":"train","x":0.1,"t":0.0,"target":0.52}]'
            ></textarea>
            <button class="action-btn primary full-width" @click="submitRows">写入表数据</button>
          </div>

          <div class="editor-card">
            <div class="section-header compact">
              <div>
                <h3>CSV 导入</h3>
                <p class="section-caption">首行必须是表头，适合批量导入。</p>
              </div>
            </div>
            <textarea
              v-model="csvEditor"
              class="tech-textarea"
              placeholder="split,x,t,target&#10;train,0.1,0.0,0.52"
            ></textarea>
            <button class="action-btn primary full-width" @click="submitCsv">导入 CSV</button>
          </div>
        </div>
      </section>
    </div>

    <section v-if="tablePreview" class="surface-card">
      <div class="section-header">
        <div>
          <h3>表数据预览</h3>
          <p class="section-caption">{{ tablePreview.database }} / {{ tablePreview.table }}</p>
        </div>
      </div>

      <div class="preview-shell">
        <div class="preview-columns">
          <span v-for="column in tablePreview.columns" :key="column.name" class="pill">
            {{ column.name }} · {{ column.type }}
          </span>
        </div>

        <div v-if="tablePreview.rows.length === 0" class="empty-state">当前表还没有数据。</div>
        <div v-else class="preview-table">
          <table>
            <thead>
              <tr>
                <th v-for="column in tablePreview.columns" :key="column.name">{{ column.name }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, index) in tablePreview.rows" :key="index">
                <td v-for="column in tablePreview.columns" :key="column.name">
                  {{ formatCell(row[column.name]) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { i18n } from '../locales'
import {
  createDatabaseProfile,
  createDatabaseSchema,
  createDatabaseTable,
  fetchDatabaseSchema,
  fetchTablePreview,
  getApiErrorMessage,
  importTableCsv,
  insertTableRows,
  listDatabaseProfiles,
  testDatabaseProfile
} from '../api/tasks'

const t = (key) => i18n.t(key)

const profiles = ref([])
const selectedProfile = ref(null)
const schema = ref({ databases: [] })
const tablePreview = ref(null)
const errorMessage = ref('')
const successMessage = ref('')

const profileForm = ref({
  name: '本地 PINNSOLVER',
  db_type: 'mysql',
  host: '127.0.0.1',
  port: 3306,
  username: 'root',
  password: '',
  default_database: 'PINNSOLVER',
  ssh_enabled: false,
  ssh_host: '',
  ssh_port: 22,
  ssh_username: '',
  ssh_password: '',
  ssh_pkey_path: '',
  ssh_pkey_passphrase: '',
  save_password: true
})

const createDatabaseForm = ref({
  database_name: 'PINNSOLVER'
})

const tableForm = ref({
  database_name: 'PINNSOLVER',
  table_name: 'training_samples',
  columns: [
    { name: 'id', type: 'INT', primary_key: true, nullable: false },
    { name: 'split', type: 'VARCHAR(32)', primary_key: false, nullable: true },
    { name: 'x', type: 'DOUBLE', primary_key: false, nullable: true },
    { name: 't', type: 'DOUBLE', primary_key: false, nullable: true },
    { name: 'target', type: 'DOUBLE', primary_key: false, nullable: true }
  ]
})

const rowEditor = ref('[{"split":"train","x":0.1,"t":0.0,"target":0.52}]')
const csvEditor = ref('split,x,t,target\ntrain,0.1,0.0,0.52')

const databaseCount = computed(() => schema.value.databases.length)
const tableCount = computed(() => schema.value.databases.reduce((total, database) => total + database.tables.length, 0))

const resetMessage = () => {
  errorMessage.value = ''
  successMessage.value = ''
}

const refreshProfiles = async () => {
  try {
    const response = await listDatabaseProfiles()
    profiles.value = response.items || []
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error)
  }
}

const submitProfile = async () => {
  resetMessage()
  try {
    const profile = await createDatabaseProfile(profileForm.value)
    successMessage.value = `连接 ${profile.name} 已保存`
    await refreshProfiles()
    await selectProfile(profile)
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error)
  }
}

const selectProfile = async (profile) => {
  selectedProfile.value = profile
  tablePreview.value = null
  tableForm.value.database_name = profile.default_database || tableForm.value.database_name
  createDatabaseForm.value.database_name = profile.default_database || createDatabaseForm.value.database_name
  await loadSchema()
}

const runConnectionTest = async () => {
  if (!selectedProfile.value) return
  resetMessage()
  try {
    await testDatabaseProfile(selectedProfile.value.profile_id)
    successMessage.value = `连接 ${selectedProfile.value.name} 测试成功`
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error)
  }
}

const loadSchema = async () => {
  if (!selectedProfile.value) return
  resetMessage()
  try {
    const response = await fetchDatabaseSchema(selectedProfile.value.profile_id)
    schema.value = response
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error)
  }
}

const submitCreateDatabase = async () => {
  if (!selectedProfile.value) return
  resetMessage()
  try {
    const response = await createDatabaseSchema(selectedProfile.value.profile_id, createDatabaseForm.value)
    schema.value = response
    successMessage.value = `数据库 ${createDatabaseForm.value.database_name} 已创建`
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error)
  }
}

const addColumn = () => {
  tableForm.value.columns.push({
    name: '',
    type: 'VARCHAR(255)',
    primary_key: false,
    nullable: true
  })
}

const submitCreateTable = async () => {
  if (!selectedProfile.value) return
  resetMessage()
  try {
    const response = await createDatabaseTable(selectedProfile.value.profile_id, tableForm.value)
    tablePreview.value = response
    successMessage.value = `表 ${tableForm.value.table_name} 已创建`
    await loadSchema()
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error)
  }
}

const submitRows = async () => {
  if (!selectedProfile.value) return
  resetMessage()
  try {
    const rows = JSON.parse(rowEditor.value)
    tablePreview.value = await insertTableRows(selectedProfile.value.profile_id, {
      database_name: tableForm.value.database_name,
      table_name: tableForm.value.table_name,
      rows
    })
    successMessage.value = `已写入 ${rows.length} 条数据`
  } catch (error) {
    errorMessage.value = error instanceof SyntaxError ? 'JSON 行数据格式错误' : getApiErrorMessage(error)
  }
}

const submitCsv = async () => {
  if (!selectedProfile.value) return
  resetMessage()
  try {
    tablePreview.value = await importTableCsv(selectedProfile.value.profile_id, {
      database_name: tableForm.value.database_name,
      table_name: tableForm.value.table_name,
      csv_text: csvEditor.value
    })
    successMessage.value = 'CSV 已导入'
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error)
  }
}

const openTable = async (databaseName, tableName) => {
  if (!selectedProfile.value) return
  resetMessage()
  tableForm.value.database_name = databaseName
  tableForm.value.table_name = tableName
  try {
    tablePreview.value = await fetchTablePreview(selectedProfile.value.profile_id, databaseName, tableName)
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error)
  }
}

const formatCell = (value) => {
  if (value === null || value === undefined) return '--'
  if (typeof value === 'object') return JSON.stringify(value)
  return value
}

onMounted(async () => {
  await refreshProfiles()
  if (profiles.value.length > 0) {
    await selectProfile(profiles.value[0])
  }
})
</script>

<style scoped>
.database-view {
  gap: 24px;
}

.workspace-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 24px;
}

.login-card {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0.02)), var(--bg-elevated);
}

.page-header,
.section-header,
.actions,
.database-head,
.toggle-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.section-header.compact {
  margin-bottom: 0.75rem;
}

.section-header h3 {
  color: var(--text-main);
  font-size: 1.15rem;
}

.section-caption {
  color: var(--text-soft);
  line-height: 1.6;
}

.form-grid,
.editor-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.mode-switch {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 22px;
  margin-bottom: 28px;
}

.mode-card {
  border: none;
  background: transparent;
  color: var(--text-soft);
  display: grid;
  justify-items: center;
  gap: 6px;
  min-width: 120px;
}

.mode-card.active {
  color: var(--text-main);
}

.mode-icon {
  font-size: 2rem;
  opacity: 0.8;
}

.mode-title {
  font-size: 0.95rem;
}

.mode-divider {
  width: 120px;
  height: 2px;
  background: rgba(255, 255, 255, 0.12);
}

.login-form {
  width: min(820px, 100%);
  margin: 0 auto;
  display: grid;
  gap: 10px;
}

.form-row {
  display: grid;
  grid-template-columns: 180px minmax(0, 1fr);
  align-items: center;
  gap: 18px;
}

.form-row label {
  color: var(--text-main);
  font-size: 0.95rem;
  letter-spacing: 0;
  text-transform: none;
  font-weight: 500;
}

.split-row {
  grid-template-columns: 180px 140px;
}

.narrow-input {
  max-width: 140px;
}

.save-secret,
.ssh-toggle {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-left: 198px;
  color: var(--text-main);
}

.save-secret input,
.ssh-toggle input {
  accent-color: var(--accent);
}

.ssh-panel {
  margin-top: 6px;
  padding-top: 12px;
  border-top: 1px dashed rgba(255, 255, 255, 0.1);
  display: grid;
  gap: 10px;
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
}

.form-section.wide {
  grid-column: span 2;
}

.form-end {
  justify-content: end;
}

label {
  color: var(--accent-strong);
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  font-weight: 700;
}

.tech-input,
.tech-textarea {
  width: 100%;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--line-soft);
  color: var(--text-main);
  border-radius: 14px;
  padding: 0.92rem 1rem;
}

.tech-textarea {
  min-height: 220px;
  resize: vertical;
}

.tech-input:focus,
.tech-textarea:focus {
  outline: none;
  border-color: rgba(139, 225, 255, 0.55);
  box-shadow: 0 0 0 4px rgba(87, 184, 255, 0.12);
}

.toggle-row,
.mini-toggle {
  margin-top: 16px;
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  color: var(--text-main);
}

.toggle-row input,
.mini-toggle input {
  accent-color: var(--accent);
}

.profile-list,
.database-list,
.column-builder {
  display: grid;
  gap: 12px;
}

.profile-card,
.database-card,
.column-row,
.editor-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 18px;
}

.profile-card {
  text-align: left;
  padding: 16px;
  display: grid;
  gap: 0.35rem;
  color: var(--text-main);
  cursor: pointer;
}

.profile-card span {
  color: var(--text-soft);
  font-size: 0.92rem;
}

.profile-card.active {
  border-color: rgba(255, 179, 107, 0.35);
  box-shadow: 0 14px 28px rgba(0, 0, 0, 0.18);
}

.database-card,
.editor-card {
  padding: 16px;
}

.table-chip-row,
.preview-columns {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 12px;
}

.table-chip,
.pill {
  border-radius: 999px;
  border: 1px solid var(--line-soft);
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-main);
  padding: 0.55rem 0.9rem;
}

.table-chip {
  cursor: pointer;
}

.column-row {
  padding: 12px;
  display: grid;
  grid-template-columns: 1.1fr 1.1fr 0.7fr 0.7fr;
  gap: 10px;
  align-items: center;
}

.action-btn,
.ghost-btn {
  border-radius: 16px;
  padding: 0.9rem 1.15rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.25s ease;
}

.ghost-btn {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--line-soft);
  color: var(--text-main);
}

.action-btn {
  border: 1px solid transparent;
}

.action-btn.primary {
  background: linear-gradient(135deg, var(--accent-warm), var(--accent));
  color: #07111f;
}

.action-btn.secondary {
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-main);
  border-color: var(--line-soft);
}

.full-width {
  width: 100%;
}

.error-box,
.note-box,
.empty-state {
  padding: 16px 18px;
  border-radius: 18px;
}

.error-box {
  background: rgba(255, 143, 143, 0.12);
  border: 1px solid rgba(255, 143, 143, 0.28);
  color: var(--danger);
}

.note-box {
  background: rgba(255, 179, 107, 0.12);
  border: 1px solid rgba(255, 179, 107, 0.24);
  color: #ffd7ae;
}

.empty-state {
  background: rgba(255, 255, 255, 0.03);
  color: var(--text-soft);
  text-align: center;
}

.preview-shell {
  display: grid;
  gap: 16px;
}

.preview-table {
  overflow: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  padding: 12px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  text-align: left;
}

th {
  color: var(--accent-strong);
  font-size: 0.82rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

td {
  color: var(--text-main);
}

@media (max-width: 980px) {
  .workspace-grid,
  .form-grid,
  .editor-grid {
    grid-template-columns: 1fr;
  }

  .form-row,
  .split-row {
    grid-template-columns: 1fr;
  }

  .save-secret,
  .ssh-toggle {
    margin-left: 0;
  }

  .form-section.wide {
    grid-column: span 1;
  }

  .column-row {
    grid-template-columns: 1fr;
  }
}
</style>
