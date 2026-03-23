import { useState, useEffect } from 'react';
import axios from 'axios';
import { useParams, Link } from 'react-router-dom';
import { Activity, CheckCircle, XCircle, AlertTriangle, ChevronLeft } from 'lucide-react';

export default function TenderDetail() {
  const { id } = useParams();
  const [tender, setTender] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const tenderRes = await axios.get(`/api/tenders/${id}`);
        setTender(tenderRes.data);
        
        // Try to get existing analysis
        try {
          const analysisRes = await axios.post(`/api/analysis/${id}`);
          if (analysisRes.data) {
            setAnalysisResult(analysisRes.data);
          }
        } catch (e) {
          // Ignore
        }
      } catch (error) {
        console.error("Error loading tender details", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [id]);

  const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
      const response = await axios.post(`/api/analysis/${id}`);
      setAnalysisResult(response.data);
    } catch (error) {
      alert('分析失败');
    } finally {
      setAnalyzing(false);
    }
  };

  if (loading) return <div className="p-8">加载中...</div>;
  if (!tender) return <div className="p-8">未找到公告</div>;

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-6">
      <Link to="/" className="text-gray-500 hover:text-gray-900 flex items-center gap-2 mb-4">
        <ChevronLeft className="w-4 h-4" /> 返回列表
      </Link>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
        <div className="flex justify-between items-start mb-6">
          <h1 className="text-2xl font-bold text-gray-900 leading-tight max-w-3xl">
            {tender.clean_title || tender.title}
          </h1>
          <span className="bg-blue-100 text-blue-800 text-xs font-semibold px-2.5 py-0.5 rounded">
            {tender.publish_date}
          </span>
        </div>

        <div className="grid grid-cols-2 gap-6 text-sm mb-8 border-b border-gray-100 pb-8">
          <div>
            <span className="text-gray-500 block mb-1">截止时间</span>
            <span className="font-medium">{tender.deadline || '详见公告'}</span>
          </div>
          <div>
            <span className="text-gray-500 block mb-1">来源链接</span>
            <a href={tender.url} target="_blank" className="text-blue-600 hover:underline truncate block">
              {tender.url}
            </a>
          </div>
        </div>

        <div className="prose prose-sm max-w-none text-gray-600 bg-gray-50 p-6 rounded-lg">
          <h3 className="text-gray-900 font-semibold mb-2">公告摘要</h3>
          <div className="whitespace-pre-wrap leading-relaxed">
            {tender.content ? tender.content.slice(0, 2000) + (tender.content.length > 2000 ? '...' : '') : '暂无内容'}
          </div>
        </div>
      </div>

      {/* Analysis Section */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
            <Activity className="w-6 h-6 text-purple-600" /> 智能商机分析
          </h2>
          {!analysisResult && (
            <button 
              onClick={handleAnalyze}
              disabled={analyzing}
              className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-lg font-medium transition-colors disabled:opacity-50"
            >
              {analyzing ? 'AI分析中...' : '生成分析报告'}
            </button>
          )}
        </div>

        {analyzing && (
           <div className="py-12 flex justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
           </div>
        )}

        {analysisResult && (
          <div className="space-y-8 animate-fade-in">
            {/* Score Banner */}
            <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-xl p-6 border border-purple-100 flex items-center gap-8">
               <div className="text-center">
                  <div className="text-4xl font-bold text-purple-700">{analysisResult.match_result.total_score}</div>
                  <div className="text-sm text-purple-600 font-medium uppercase tracking-wide mt-1">匹配得分</div>
               </div>
               <div className="h-12 w-px bg-purple-200"></div>
               <div>
                  <div className="font-bold text-lg text-gray-900 flex items-center gap-2 mb-1">
                    {analysisResult.match_result.recommendation}
                    {analysisResult.match_result.total_score >= 80 ? (
                        <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : analysisResult.match_result.total_score >= 50 ? (
                        <AlertTriangle className="w-5 h-5 text-yellow-500" />
                    ) : (
                        <XCircle className="w-5 h-5 text-red-500" />
                    )}
                  </div>
                  <p className="text-gray-600 text-sm">
                    {analysisResult.match_result.match_details.join('；')}
                  </p>
               </div>
            </div>

            {/* Analysis Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="p-5 bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow">
                    <h4 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-red-500"></span> 风险评估
                    </h4>
                    <p className="text-gray-600 text-sm leading-relaxed">{analysisResult.ai_analysis.risk_assessment}</p>
                </div>
                <div className="p-5 bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow">
                    <h4 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-yellow-500"></span> 竞争对手分析
                    </h4>
                    <p className="text-gray-600 text-sm leading-relaxed">{analysisResult.ai_analysis.competitor_analysis}</p>
                </div>
                <div className="p-5 bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow">
                    <h4 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-blue-500"></span> 技术难度
                    </h4>
                    <p className="text-gray-600 text-sm leading-relaxed">{analysisResult.ai_analysis.technical_difficulty}</p>
                </div>
                <div className="p-5 bg-blue-50 border border-blue-100 rounded-lg shadow-sm">
                    <h4 className="font-semibold text-blue-800 mb-3 flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-blue-600"></span> 总结建议
                    </h4>
                    <p className="text-blue-700 text-sm leading-relaxed font-medium">{analysisResult.ai_analysis.summary}</p>
                </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
