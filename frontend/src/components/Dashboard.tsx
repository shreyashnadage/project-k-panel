'use client'

import { useDashboardStore } from '@/lib/store'
import { WIDGET_DEFINITIONS, DEFAULT_LAYOUTS } from '@/lib/widgetRegistry'
import { RefreshCw, BarChart3, Users, TrendingUp, Activity, Zap, Settings } from 'lucide-react'

export default function Dashboard() {
  const { currentPage, setCurrentPage, auth } = useDashboardStore()
  const userRole = (auth?.role || 'viewer') as keyof typeof DEFAULT_LAYOUTS

  const layout = DEFAULT_LAYOUTS[userRole] || []

  const navItems = [
    { id: 'overview', label: 'Overview', icon: BarChart3, active: currentPage === 'overview' },
    { id: 'tally-sync', label: 'Tally Sync', icon: RefreshCw, active: currentPage === 'tally-sync' },
    { id: 'msme', label: 'MSMEs', icon: Users, active: currentPage === 'msme' },
    { id: 'treds', label: 'GST & TReDS', icon: TrendingUp, active: currentPage === 'treds' },
    { id: 'activity', label: 'Activity', icon: Activity, active: currentPage === 'activity' },
    { id: 'health', label: 'Health', icon: Zap, active: currentPage === 'health' },
    { id: 'settings', label: 'Settings', icon: Settings, active: currentPage === 'settings' },
  ]

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-slate-950/80 backdrop-blur-xl border-b border-slate-800">
        <div className="flex items-center justify-between px-8 py-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-br from-teal-500 to-teal-600 rounded-lg flex items-center justify-center text-white font-bold text-sm">
              TS
            </div>
            <h1 className="text-xl font-semibold text-slate-50">Tally Sync</h1>
          </div>
          <div className="text-sm text-slate-400">
            Role: <span className="text-teal-400 font-medium capitalize">{userRole}</span>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar Navigation */}
        <aside className="w-64 border-r border-slate-800 p-6">
          <nav className="space-y-2">
            {navItems.map((item) => {
              const Icon = item.icon
              return (
                <button
                  key={item.id}
                  onClick={() => setCurrentPage(item.id as any)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition ${
                    item.active
                      ? 'bg-teal-600/20 text-teal-400 border border-teal-500/30'
                      : 'text-slate-400 hover:bg-slate-800'
                  }`}
                >
                  <Icon size={18} />
                  <span className="text-sm font-medium">{item.label}</span>
                  {item.active && <div className="ml-auto w-2 h-2 rounded-full bg-teal-400" />}
                </button>
              )
            })}
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-8">
          {/* Overview Page */}
          {currentPage === 'overview' && (
            <div className="space-y-8">
              <div>
                <h2 className="text-2xl font-bold text-slate-50 mb-2">Dashboard Overview</h2>
                <p className="text-slate-400">Real-time sync metrics and financial insights</p>
              </div>

              {/* Widgets Grid */}
              <div className="grid gap-6 grid-cols-1 lg:grid-cols-3">
                {layout.map((widgetConfig) => {
                  const Widget = widgetConfig.component
                  return (
                    <div
                      key={widgetConfig.id}
                      className={
                        widgetConfig.size === 'full'
                          ? 'lg:col-span-3'
                          : widgetConfig.size === 'large'
                            ? 'lg:col-span-2'
                            : 'lg:col-span-1'
                      }
                    >
                      <Widget />
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Other Pages (Placeholders) */}
          {currentPage === 'tally-sync' && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-slate-50">Tally Sync Status</h2>
              <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-8 text-center">
                <p className="text-slate-400">Detailed Tally synchronization status and history.</p>
              </div>
            </div>
          )}

          {currentPage === 'msme' && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-slate-50">MSME Connections</h2>
              <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-8 text-center">
                <p className="text-slate-400">Manage connected MSME companies and integrations.</p>
              </div>
            </div>
          )}

          {currentPage === 'treds' && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-slate-50">GST & TReDS</h2>
              <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-8 text-center">
                <p className="text-slate-400">GST compliance and TReDS invoice discounting.</p>
              </div>
            </div>
          )}

          {currentPage === 'activity' && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-slate-50">Activity History</h2>
              <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-8 text-center">
                <p className="text-slate-400">Complete sync activity and audit logs.</p>
              </div>
            </div>
          )}

          {currentPage === 'health' && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-slate-50">System Health</h2>
              <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-8 text-center">
                <p className="text-slate-400">Detailed system health monitoring and status.</p>
              </div>
            </div>
          )}

          {currentPage === 'settings' && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-slate-50">Settings</h2>
              <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-8 text-center">
                <p className="text-slate-400">Dashboard and system configuration.</p>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
