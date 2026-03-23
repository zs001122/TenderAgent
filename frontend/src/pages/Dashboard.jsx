import { useState, useEffect } from 'react';
import axios from 'axios';
import { FileText, TrendingUp, DollarSign, Award, ChevronRight } from 'lucide-react';
import { Link } from 'react-router-dom';

function StatsCard({ title, value, icon: Icon, color }) {
  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 flex items-center justify-between">
      <div>
        <p className="text-sm text-gray-500 mb-1">{title}</p>
        <h3 className="text-2xl font-bold text-gray-900">{value}</h3>
      </div>
      <div className={`p-3 rounded-lg ${color}`}>
        <Icon className="w-6 h-6 text-white" />
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [tenders, setTenders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, tendersRes] = await Promise.all([
          axios.get('/api/dashboard/stats'),
          axios.get('/api/tenders/?limit=10')
        ]);
        setStats(statsRes.data);
        setTenders(tendersRes.data.items);
      } catch (error) {
        console.error("Error loading dashboard data", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <div className="p-8">加载中...</div>;

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Top Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatsCard 
          title="总招标公告" 
          value={stats?.total_tenders || 0} 
          icon={FileText} 
          color="bg-blue-500" 
        />
        <StatsCard 
          title="已智能分析" 
          value={stats?.analyzed_count || 0} 
          icon={TrendingUp} 
          color="bg-purple-500" 
        />
        <StatsCard 
          title="高价值商机 (>500万)" 
          value={stats?.high_value_count || 0} 
          icon={DollarSign} 
          color="bg-green-500" 
        />
        <StatsCard 
          title="涉及总金额 (万元)" 
          value={stats?.total_budget_wanyuan || 0} 
          icon={Award} 
          color="bg-orange-500" 
        />
      </div>

      {/* Recent Tenders Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <h2 className="font-bold text-gray-800">最新招标公告</h2>
          <Link to="/" className="text-sm text-blue-600 hover:underline">查看全部</Link>
        </div>
        <table className="w-full text-left">
          <thead className="bg-gray-50 text-gray-500 text-xs uppercase">
            <tr>
              <th className="px-6 py-3">标题</th>
              <th className="px-6 py-3">发布时间</th>
              <th className="px-6 py-3">截止时间</th>
              <th className="px-6 py-3">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {tenders.map((tender) => (
              <tr key={tender.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-6 py-4">
                  <div className="font-medium text-gray-900 truncate max-w-md" title={tender.clean_title}>
                    {tender.clean_title || tender.title}
                  </div>
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">{tender.publish_date}</td>
                <td className="px-6 py-4 text-sm text-gray-500">{tender.deadline || '-'}</td>
                <td className="px-6 py-4">
                  <Link 
                    to={`/tender/${tender.id}`} 
                    className="text-blue-600 hover:text-blue-800 text-sm font-medium flex items-center gap-1"
                  >
                    详情 <ChevronRight className="w-4 h-4" />
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
