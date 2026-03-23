import { Link } from 'react-router-dom';
import { LayoutDashboard, FileText, Settings, Activity } from 'lucide-react';

export default function Sidebar() {
  return (
    <div className="w-64 bg-gray-900 text-white min-h-screen flex flex-col">
      <div className="p-6 flex items-center gap-3 border-b border-gray-800">
        <Activity className="w-8 h-8 text-blue-500" />
        <span className="text-xl font-bold tracking-tight">TenderAgent</span>
      </div>
      
      <nav className="flex-1 p-4 space-y-2">
        <Link to="/" className="flex items-center gap-3 px-4 py-3 text-gray-300 hover:bg-gray-800 rounded-lg transition-colors">
          <LayoutDashboard className="w-5 h-5" />
          <span>仪表盘</span>
        </Link>
        <Link to="/" className="flex items-center gap-3 px-4 py-3 text-gray-300 hover:bg-gray-800 rounded-lg transition-colors">
          <FileText className="w-5 h-5" />
          <span>招标公告</span>
        </Link>
        <div className="pt-4 border-t border-gray-800 mt-4">
            <div className="px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">系统设置</div>
            <Link to="#" className="flex items-center gap-3 px-4 py-3 text-gray-300 hover:bg-gray-800 rounded-lg transition-colors">
              <Settings className="w-5 h-5" />
              <span>配置管理</span>
            </Link>
        </div>
      </nav>
      
      <div className="p-4 border-t border-gray-800">
        <div className="text-xs text-gray-500">v1.0.0 Demo</div>
      </div>
    </div>
  );
}
