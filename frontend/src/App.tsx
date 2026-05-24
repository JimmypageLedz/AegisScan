import { useEffect, useMemo, useState } from 'react'

import './App.css'

const navItems = [
  { key: 'Dashboard', label: '总览' },
  { key: 'Assets', label: '资产' },
  { key: 'Tasks', label: '任务' },
  { key: 'Findings', label: '发现' },
  { key: 'Reports', label: '报告' },
  { key: 'Settings', label: '设置' },
] as const

const fallbackModels = ['gpt-4.1-mini', 'gpt-4.1'] as const

type ViewName = (typeof navItems)[number]['key']
type ReportMode = 'mock' | 'real' | 'auto'

const modeOptions: { value: ReportMode; label: string }[] = [
  { value: 'mock', label: '模拟模式' },
  { value: 'real', label: '真实模型' },
  { value: 'auto', label: '自动选择' },
]

const modelLabels: Record<string, string> = {
  'gpt-4.1-mini': 'GPT-4.1 Mini',
  'gpt-4.1': 'GPT-4.1',
}

const taskStatusLabels: Record<string, string> = {
  pending: '等待中',
  running: '扫描中',
  finished: '已完成',
  failed: '失败',
}

const severityLabels: Record<string, string> = {
  high: '高危',
  medium: '中危',
  low: '低危',
  info: '提示',
}

const confidenceLabels: Record<string, string> = {
  high: '高',
  medium: '中',
  low: '低',
}

type ReportData = {
  id: number
  task_id: number
  summary: string
  severity: string
  impact: string
  remediation: string
  confidence: string
  model_name: string | null
  raw_output: string | null
}

type TaskData = {
  id: number
  asset_id: number
  status: string
}

type AssetData = {
  id: number
  name: string
  target_url: string
  description: string | null
}

type FindingData = {
  id: number
  task_id: number
  title: string
  severity: string
  evidence: string | null
  recommendation: string | null
}

type ModelListData = {
  models: string[]
  default_model: string | null
  source: string
  warning: string | null
}

class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

const viewMeta: Record<
  ViewName,
  {
    eyebrow: string
    title: string
    description: string
  }
> = {
  Dashboard: {
    eyebrow: '总览',
    title: '安全态势面板',
    description: '查看资产数量、扫描任务和当前最明显的风险聚合。',
  },
  Assets: {
    eyebrow: '资产清单',
    title: '资产管理',
    description: '登记目标地址，并决定哪些端点进入扫描范围。',
  },
  Tasks: {
    eyebrow: '执行队列',
    title: '扫描任务',
    description: '发起扫描、查看任务状态，并观察 Redis/Celery 的执行流。',
  },
  Findings: {
    eyebrow: '扫描结果',
    title: '发现结果',
    description: '查看扫描器输出、风险等级和每个问题对应的证据。',
  },
  Reports: {
    eyebrow: '风险分析',
    title: '风险报告',
    description: '根据发现结果生成结构化总结，并对比不同模型的报告质量。',
  },
  Settings: {
    eyebrow: '模型路由',
    title: '提供方设置',
    description: '配置后端接口地址，并选择报告生成方式。',
  },
}

function formatTaskStatus(status: string) {
  return taskStatusLabels[status] ?? status
}

function formatSeverity(severity: string) {
  return severityLabels[severity] ?? severity
}

function formatConfidence(confidence: string) {
  return confidenceLabels[confidence] ?? confidence
}

function App() {
  const [activeView, setActiveView] = useState<ViewName>('Dashboard')
  const [baseUrl, setBaseUrl] = useState('http://127.0.0.1:8000')
  const [apiKey, setApiKey] = useState('')
  const [mode, setMode] = useState<ReportMode>('mock')
  const [model, setModel] = useState<string>('')
  const [availableModels, setAvailableModels] = useState<string[]>([...fallbackModels])
  const [taskId, setTaskId] = useState('14')
  const [newTaskAssetId, setNewTaskAssetId] = useState('')
  const [tasks, setTasks] = useState<TaskData[]>([])
  const [assets, setAssets] = useState<AssetData[]>([])
  const [findings, setFindings] = useState<FindingData[]>([])
  const [report, setReport] = useState<ReportData | null>(null)
  const [assetName, setAssetName] = useState('')
  const [assetUrl, setAssetUrl] = useState('')
  const [assetDescription, setAssetDescription] = useState('')
  const [statusMessage, setStatusMessage] = useState('工作区已就绪。')
  const [isLoading, setIsLoading] = useState(false)

  const currentView = viewMeta[activeView]

  const requestHeaders = useMemo(() => {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }

    if (apiKey.trim()) {
      headers.Authorization = `Bearer ${apiKey.trim()}`
    }

    return headers
  }, [apiKey])

  async function requestJson<T>(url: string, options?: RequestInit) {
    const response = await fetch(url, options)
    const data = await response.json().catch(() => null)

    if (!response.ok) {
      const detail = typeof data?.detail === 'string' ? data.detail : '请求失败。'
      throw new ApiError(response.status, detail)
    }

    return data as T
  }

  async function deleteJson(url: string) {
    const response = await fetch(url, {
      method: 'DELETE',
      headers: requestHeaders,
    })
    const data = await response.json().catch(() => null)

    if (!response.ok) {
      const detail = typeof data?.detail === 'string' ? data.detail : '删除失败。'
      throw new ApiError(response.status, detail)
    }
  }

  async function fetchTasks() {
    try {
      const data = await requestJson<TaskData[]>(`${baseUrl}/tasks`, {
        headers: requestHeaders,
      })
      setTasks(data)
      setStatusMessage(`已加载 ${data.length} 个任务。`)
    }
    catch (error) {
      const message = error instanceof Error ? error.message : '加载任务时发生未知错误。'
      setStatusMessage(message)
    }
  }

  async function fetchAssets() {
    try {
      const data = await requestJson<AssetData[]>(`${baseUrl}/assets`, {
        headers: requestHeaders,
      })
      setAssets(data)
      setStatusMessage(`已加载 ${data.length} 个资产。`)
    }
    catch (error) {
      const message = error instanceof Error ? error.message : '加载资产时发生未知错误。'
      setStatusMessage(message)
    }
  }

  async function fetchModels() {
    setIsLoading(true)
    setStatusMessage('正在获取模型列表...')

    try {
      const data = await requestJson<ModelListData>(`${baseUrl}/llm/models`, {
        headers: requestHeaders,
      })

      setAvailableModels(data.models)

      if (data.default_model && data.models.includes(data.default_model)) {
        setModel(data.default_model)
      }
      else if (!model && data.models.length > 0) {
        setModel(data.models[0])
      }

      if (data.source === 'fallback') {
        setStatusMessage(`模型列表接口被上游拦截，已使用本地回退列表（${data.models.length} 个）。`)
      }
      else {
        setStatusMessage(`已获取 ${data.models.length} 个模型。`)
      }
    }
    catch (error) {
      const message = error instanceof Error ? error.message : '获取模型列表时发生未知错误。'
      setStatusMessage(message)
    }
    finally {
      setIsLoading(false)
    }
  }

  async function fetchFindings(targetTaskId: string) {
    try {
      const data = await requestJson<FindingData[]>(
        `${baseUrl}/findings?task_id=${encodeURIComponent(targetTaskId)}`,
        {
          headers: requestHeaders,
        },
      )
      setFindings(data)
      setStatusMessage(`已加载任务 #${targetTaskId} 的 ${data.length} 条发现。`)
    }
    catch (error) {
      const message = error instanceof Error ? error.message : '加载发现结果时发生未知错误。'
      setStatusMessage(message)
    }
  }

  async function fetchReport(targetTaskId: string) {
    try {
      const data = await requestJson<ReportData>(`${baseUrl}/reports/${targetTaskId}`, {
        headers: requestHeaders,
      })
      setReport(data)
      setStatusMessage(`已加载任务 #${targetTaskId} 的报告。`)
    }
    catch (error) {
      if (error instanceof ApiError && error.status === 404) {
        setReport(null)
        setStatusMessage(`任务 #${targetTaskId} 还没有生成过报告，可以点击“生成报告”。`)
        return
      }

      const message = error instanceof Error ? error.message : '加载报告时发生未知错误。'
      setStatusMessage(message)
    }
  }

  async function handleGenerateReport() {
    const trimmedTaskId = taskId.trim()
    if (!trimmedTaskId) {
      setStatusMessage('生成报告前需要填写任务 ID。')
      return
    }

    setIsLoading(true)
    setStatusMessage('正在生成报告...')

    try {
      const data = await requestJson<ReportData>(`${baseUrl}/reports/${trimmedTaskId}/generate`, {
        method: 'POST',
        headers: requestHeaders,
        body: JSON.stringify({
          mode,
          model: model || null,
        }),
      })

      setReport(data)
      setActiveView('Reports')
      setStatusMessage(`已生成任务 #${trimmedTaskId} 的报告。`)
    }
    catch (error) {
      const message = error instanceof Error ? error.message : '生成报告时发生未知错误。'
      setStatusMessage(message)
    }
    finally {
      setIsLoading(false)
    }
  }

  async function handleCreateAsset() {
    if (!assetName.trim() || !assetUrl.trim()) {
      setStatusMessage('资产名称和目标 URL 必填。')
      return
    }

    setIsLoading(true)
    setStatusMessage('正在创建资产...')

    try {
      await requestJson<AssetData>(`${baseUrl}/assets`, {
        method: 'POST',
        headers: requestHeaders,
        body: JSON.stringify({
          name: assetName.trim(),
          target_url: assetUrl.trim(),
          description: assetDescription.trim() || null,
        }),
      })

      setAssetName('')
      setAssetUrl('')
      setAssetDescription('')
      await fetchAssets()
      setStatusMessage('资产创建成功。')
    }
    catch (error) {
      const message = error instanceof Error ? error.message : '创建资产时发生未知错误。'
      setStatusMessage(message)
    }
    finally {
      setIsLoading(false)
    }
  }

  async function handleCreateTask(assetId: number) {
    setIsLoading(true)
    setStatusMessage(`正在为资产 #${assetId} 创建任务...`)

    try {
      const data = await requestJson<TaskData>(`${baseUrl}/tasks`, {
        method: 'POST',
        headers: requestHeaders,
        body: JSON.stringify({
          asset_id: assetId,
        }),
      })

      setTaskId(String(data.id))
      await fetchTasks()
      setStatusMessage(`已为资产 #${assetId} 创建任务 #${data.id}。`)
      setActiveView('Tasks')
    }
    catch (error) {
      const message = error instanceof Error ? error.message : '创建任务时发生未知错误。'
      setStatusMessage(message)
    }
    finally {
      setIsLoading(false)
    }
  }

  function handleSelectTask(task: TaskData) {
    setTaskId(String(task.id))
    setStatusMessage(`已选择任务 #${task.id}。`)
  }

  async function handleDeleteAsset(assetId: number) {
    if (!window.confirm(`确定删除资产 #${assetId} 吗？相关任务、发现和报告也会一起删除。`)) {
      return
    }

    setIsLoading(true)
    setStatusMessage(`正在删除资产 #${assetId}...`)

    try {
      await deleteJson(`${baseUrl}/assets/${assetId}`)
      await fetchAssets()
      await fetchTasks()
      setFindings([])
      setReport(null)
      setStatusMessage(`已删除资产 #${assetId}。`)
    }
    catch (error) {
      const message = error instanceof Error ? error.message : '删除资产时发生未知错误。'
      setStatusMessage(message)
    }
    finally {
      setIsLoading(false)
    }
  }

  async function handleDeleteTask(targetTaskId: number) {
    if (!window.confirm(`确定删除任务 #${targetTaskId} 吗？相关发现和报告也会一起删除。`)) {
      return
    }

    setIsLoading(true)
    setStatusMessage(`正在删除任务 #${targetTaskId}...`)

    try {
      await deleteJson(`${baseUrl}/tasks/${targetTaskId}`)
      await fetchTasks()
      setFindings((currentFindings) =>
        currentFindings.filter((finding) => finding.task_id !== targetTaskId),
      )

      if (taskId === String(targetTaskId)) {
        setTaskId('')
        setReport(null)
      }

      setStatusMessage(`已删除任务 #${targetTaskId}。`)
    }
    catch (error) {
      const message = error instanceof Error ? error.message : '删除任务时发生未知错误。'
      setStatusMessage(message)
    }
    finally {
      setIsLoading(false)
    }
  }

  async function handleDeleteFinding(findingId: number) {
    if (!window.confirm(`确定删除发现 #${findingId} 吗？`)) {
      return
    }

    setIsLoading(true)
    setStatusMessage(`正在删除发现 #${findingId}...`)

    try {
      await deleteJson(`${baseUrl}/findings/${findingId}`)
      setFindings((currentFindings) =>
        currentFindings.filter((finding) => finding.id !== findingId),
      )
      setStatusMessage(`已删除发现 #${findingId}。`)
    }
    catch (error) {
      const message = error instanceof Error ? error.message : '删除发现时发生未知错误。'
      setStatusMessage(message)
    }
    finally {
      setIsLoading(false)
    }
  }

  async function handleDeleteReport() {
    const trimmedTaskId = taskId.trim()
    if (!trimmedTaskId) {
      setStatusMessage('删除报告前需要先选择任务。')
      return
    }

    if (!window.confirm(`确定删除任务 #${trimmedTaskId} 的报告吗？`)) {
      return
    }

    setIsLoading(true)
    setStatusMessage(`正在删除任务 #${trimmedTaskId} 的报告...`)

    try {
      await deleteJson(`${baseUrl}/reports/${trimmedTaskId}`)
      setReport(null)
      setStatusMessage(`已删除任务 #${trimmedTaskId} 的报告。`)
    }
    catch (error) {
      const message = error instanceof Error ? error.message : '删除报告时发生未知错误。'
      setStatusMessage(message)
    }
    finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchTasks()
    fetchAssets()
  }, [baseUrl])

  useEffect(() => {
    const trimmedTaskId = taskId.trim()
    if (!trimmedTaskId) {
      return
    }

    if (activeView === 'Reports') {
      fetchReport(trimmedTaskId)
    }

    if (activeView === 'Findings') {
      fetchFindings(trimmedTaskId)
    }
  }, [activeView, taskId])

  const highFindingCount = findings.filter((finding) => finding.severity === 'high').length
  const finishedTaskCount = tasks.filter((task) => task.status === 'finished').length

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">AS</div>
          <div>
            <h1>AegisScan</h1>
            <p>安全扫描工作台</p>
          </div>
        </div>

        <nav className="nav">
          {navItems.map((item) => (
            <button
              key={item.key}
              type="button"
              className={`nav-item ${item.key === activeView ? 'active' : ''}`}
              onClick={() => setActiveView(item.key)}
            >
              <span className="nav-dot" />
              {item.label}
            </button>
          ))}
        </nav>

        <div className="sidebar-card">
          <span className="eyebrow">当前视图</span>
          <strong>{navItems.find((item) => item.key === activeView)?.label}</strong>
          <p>{currentView.description}</p>
        </div>
      </aside>

      <main className="content">
        <header className="topbar">
          <div>
            <span className="eyebrow">{currentView.eyebrow}</span>
            <h2>{currentView.title}</h2>
          </div>
          <div className="status-pill">后端地址：{baseUrl}</div>
        </header>

        {activeView === 'Dashboard' ? (
          <section className="grid">
            <section className="panel summary-panel">
              <span className="eyebrow">快照</span>
              <h3>当前工作区</h3>
              <div className="stats">
                <article className="stat-card">
                  <span>资产</span>
                  <strong>{assets.length}</strong>
                </article>
                <article className="stat-card">
                  <span>任务</span>
                  <strong>{tasks.length}</strong>
                </article>
                <article className="stat-card">
                  <span>已完成</span>
                  <strong>{finishedTaskCount}</strong>
                </article>
                <article className="stat-card">
                  <span>高危发现</span>
                  <strong>{highFindingCount}</strong>
                </article>
              </div>
              <div className="report-card">
                <span className="eyebrow">当前任务</span>
                <h4>{taskId ? `任务 #${taskId}` : '尚未选择任务'}</h4>
                <p>{statusMessage}</p>
              </div>
            </section>
            <section className="panel">
              <span className="eyebrow">快捷操作</span>
              <h3>下一步</h3>
              <div className="placeholder-box">
                在任务页选择一个扫描任务，查看发现结果，然后到设置页生成风险报告。
              </div>
            </section>
          </section>
        ) : null}

        {activeView === 'Settings' ? (
          <section className="grid">
            <section className="panel settings-panel">
              <div className="panel-head">
                <div>
                  <span className="eyebrow">连接配置</span>
                  <h3>接口与模型</h3>
                </div>
              </div>

              <div className="field-grid">
                <label className="field">
                  <span>后端接口地址</span>
                  <input
                    type="text"
                    value={baseUrl}
                    onChange={(event) => setBaseUrl(event.target.value)}
                  />
                </label>

                <label className="field">
                  <span>API 密钥</span>
                  <input
                    type="password"
                    value={apiKey}
                    placeholder="sk-..."
                    onChange={(event) => setApiKey(event.target.value)}
                  />
                </label>

                <label className="field">
                  <span>生成模式</span>
                  <select
                    value={mode}
                    onChange={(event) => setMode(event.target.value as ReportMode)}
                  >
                    {modeOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="field">
                  <span>模型</span>
                  <div className="inline-control">
                    <select
                      value={model}
                      onChange={(event) => setModel(event.target.value)}
                    >
                      <option value="">跟随后端默认配置</option>
                      {availableModels.map((modelItem) => (
                        <option key={modelItem} value={modelItem}>
                          {modelLabels[modelItem] ?? modelItem}
                        </option>
                      ))}
                    </select>
                    <button
                      type="button"
                      className="mini-action"
                      onClick={fetchModels}
                      disabled={isLoading}
                    >
                      获取模型
                    </button>
                  </div>
                </label>

                <label className="field field-span">
                  <span>任务 ID</span>
                  <input
                    type="text"
                    value={taskId}
                    onChange={(event) => setTaskId(event.target.value)}
                  />
                </label>
              </div>

              <div className="actions">
                <button
                  type="button"
                  className="primary"
                  onClick={() => setStatusMessage('设置已在前端暂存。')}
                >
                  保存设置
                </button>
                <button
                  type="button"
                  className="secondary"
                  onClick={handleGenerateReport}
                  disabled={isLoading}
                >
                  {isLoading ? '生成中...' : '生成报告'}
                </button>
              </div>

              <div className="inline-status">{statusMessage}</div>
            </section>

            <section className="panel summary-panel">
              <span className="eyebrow">运行概览</span>
              <h3>实时快照</h3>

              <div className="stats">
                <article className="stat-card">
                  <span>资产</span>
                  <strong>{assets.length}</strong>
                </article>
                <article className="stat-card">
                  <span>任务</span>
                  <strong>{tasks.length}</strong>
                </article>
                <article className="stat-card">
                  <span>报告</span>
                  <strong>{report ? 1 : 0}</strong>
                </article>
              </div>

              <div className="report-card">
                <span className="eyebrow">最新报告</span>
                <h4>{report ? `任务 #${report.task_id}` : '暂无已加载报告'}</h4>
                <p>
                  {report
                    ? report.summary
                    : '可以在设置面板里为已有任务生成报告。'}
                </p>
              </div>
            </section>
          </section>
        ) : null}

        {activeView === 'Assets' ? (
          <section className="grid">
            <section className="panel settings-panel">
              <div className="panel-head">
                <div>
                  <span className="eyebrow">新建</span>
                  <h3>新增资产</h3>
                </div>
              </div>

              <div className="field-grid">
                <label className="field">
                  <span>名称</span>
                  <input value={assetName} onChange={(event) => setAssetName(event.target.value)} />
                </label>

                <label className="field">
                  <span>目标 URL</span>
                  <input value={assetUrl} onChange={(event) => setAssetUrl(event.target.value)} />
                </label>

                <label className="field field-span">
                  <span>描述</span>
                  <input value={assetDescription} onChange={(event) => setAssetDescription(event.target.value)} />
                </label>
              </div>

              <div className="actions">
                <button type="button" className="primary" onClick={handleCreateAsset} disabled={isLoading}>
                  {isLoading ? '保存中...' : '创建资产'}
                </button>
                <button type="button" className="secondary" onClick={fetchAssets}>
                  刷新资产
                </button>
              </div>

              <div className="inline-status">{statusMessage}</div>
            </section>

            <section className="panel task-panel">
              <div className="task-header">
                <div>
                  <span className="eyebrow">实时数据</span>
                  <h3>资产列表</h3>
                </div>
              </div>

              <div className="task-list">
                {assets.map((asset) => (
                  <div key={asset.id} className="task-row static-row">
                    <div>
                      <strong>{asset.name}</strong>
                      <span>{asset.target_url}</span>
                    </div>
                    <div className="task-row-actions">
                      <button
                        type="button"
                        className="mini-action"
                        onClick={() => handleCreateTask(asset.id)}
                      >
                        扫描
                      </button>
                      <button
                        type="button"
                        className="mini-action danger"
                        onClick={() => handleDeleteAsset(asset.id)}
                        disabled={isLoading}
                      >
                        删除
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </section>
        ) : null}

        {activeView === 'Tasks' ? (
          <section className="panel task-panel">
            <div className="task-header">
              <div>
                <span className="eyebrow">实时数据</span>
                <h3>任务列表</h3>
              </div>
              <div className="task-actions">
                <label className="task-inline-field">
                  <span>资产</span>
                  <select
                    value={newTaskAssetId}
                    onChange={(event) => setNewTaskAssetId(event.target.value)}
                  >
                    <option value="">选择资产</option>
                    {assets.map((asset) => (
                      <option key={asset.id} value={String(asset.id)}>
                        #{asset.id} {asset.name}
                      </option>
                    ))}
                  </select>
                </label>
                <button
                  type="button"
                  className="mini-action"
                  disabled={!newTaskAssetId || isLoading}
                  onClick={() => handleCreateTask(Number(newTaskAssetId))}
                >
                  创建任务
                </button>
                <button type="button" className="secondary" onClick={fetchTasks}>
                  刷新任务
                </button>
              </div>
            </div>

            <div className="task-list">
              {tasks.map((task) => (
                <div
                  key={task.id}
                  className={`task-row ${taskId === String(task.id) ? 'selected' : ''}`}
                >
                  <div>
                    <strong>任务 #{task.id}</strong>
                    <span>资产 #{task.asset_id}</span>
                  </div>
                  <div className="task-row-actions">
                    <span className="task-status">{formatTaskStatus(task.status)}</span>
                    <button
                      type="button"
                      className="mini-action"
                      onClick={() => {
                        handleSelectTask(task)
                        setActiveView('Findings')
                      }}
                    >
                      查看发现
                    </button>
                    <button
                      type="button"
                      className="mini-action"
                      onClick={() => {
                        handleSelectTask(task)
                        setActiveView('Reports')
                      }}
                    >
                      查看报告
                    </button>
                    <button
                      type="button"
                      className="mini-action danger"
                      onClick={() => handleDeleteTask(task.id)}
                      disabled={isLoading}
                    >
                      删除
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </section>
        ) : null}

        {activeView === 'Findings' ? (
          <section className="panel task-panel">
            <div className="task-header">
              <div>
                <span className="eyebrow">实时数据</span>
                <h3>任务 #{taskId} 的发现结果</h3>
              </div>
              <button
                type="button"
                className="secondary"
                onClick={() => fetchFindings(taskId.trim())}
                disabled={!taskId.trim()}
              >
                刷新发现
              </button>
            </div>

            <div className="task-list">
              {findings.map((finding) => (
                <div key={finding.id} className="task-row static-row">
                  <div>
                    <strong>{finding.title}</strong>
                    <span>{finding.evidence ?? '暂无证据。'}</span>
                  </div>
                  <div className="task-row-actions">
                    <span className="task-status">{formatSeverity(finding.severity)}</span>
                    <button
                      type="button"
                      className="mini-action danger"
                      onClick={() => handleDeleteFinding(finding.id)}
                      disabled={isLoading}
                    >
                      删除
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </section>
        ) : null}

        {activeView === 'Reports' ? (
          <section className="panel report-detail">
            <div className="task-header">
              <div>
                <span className="eyebrow">最新输出</span>
                <h3>{report ? `任务 #${report.task_id} 的报告` : '暂无已加载报告'}</h3>
              </div>
              <div className="task-row-actions">
                <button
                  type="button"
                  className="secondary"
                  onClick={() => fetchReport(taskId.trim())}
                  disabled={!taskId.trim()}
                >
                  加载已有报告
                </button>
                <button
                  type="button"
                  className="primary"
                  onClick={handleGenerateReport}
                  disabled={!taskId.trim() || isLoading}
                >
                  {isLoading ? '生成中...' : '生成报告'}
                </button>
                <button
                  type="button"
                  className="mini-action danger"
                  onClick={handleDeleteReport}
                  disabled={!report || isLoading}
                >
                  删除报告
                </button>
              </div>
            </div>
            <p className="report-meta">{statusMessage}</p>

            {report ? (
              <div className="report-grid">
                <div className="report-block">
                  <span className="eyebrow">总结</span>
                  <p>{report.summary}</p>
                </div>
                <div className="report-block">
                  <span className="eyebrow">风险等级</span>
                  <p>{formatSeverity(report.severity)}</p>
                </div>
                <div className="report-block">
                  <span className="eyebrow">影响</span>
                  <p>{report.impact}</p>
                </div>
                <div className="report-block">
                  <span className="eyebrow">修复建议</span>
                  <p>{report.remediation}</p>
                </div>
                <div className="report-block">
                  <span className="eyebrow">置信度</span>
                  <p>{formatConfidence(report.confidence)}</p>
                </div>
                <div className="report-block">
                  <span className="eyebrow">模型</span>
                  <p>{report.model_name ?? '未知'}</p>
                </div>
                {report.raw_output?.startsWith('LLM request failed') ? (
                  <div className="report-block report-block-wide">
                    <span className="eyebrow">生成状态</span>
                    <p>真实 LLM 请求被上游拦截，当前报告由本地规则降级生成。</p>
                  </div>
                ) : null}
              </div>
            ) : (
              <div className="placeholder-box">
                加载或生成所选任务的报告后，这里会显示报告内容。
              </div>
            )}
          </section>
        ) : null}
      </main>
    </div>
  )
}

export default App
