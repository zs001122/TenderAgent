import { Routes, Route, Link, useLocation } from 'react-router-dom'
import { Layout, Menu, Space, Typography, Tag } from 'antd'
import { FileTextOutlined, SettingOutlined, RadarChartOutlined } from '@ant-design/icons'
import TenderList from './pages/TenderList'
import CompanyProfile from './pages/CompanyProfile'

const { Header, Content } = Layout
const { Title, Text } = Typography

function App() {
  const location = useLocation()

  const menuItems = [
    {
      key: '/',
      icon: <FileTextOutlined />,
      label: <Link to="/">招标列表</Link>,
    },
    {
      key: '/company',
      icon: <SettingOutlined />,
      label: <Link to="/company">公司配置</Link>,
    },
  ]

  return (
    <Layout
      style={{
        minHeight: '100vh',
        background: 'linear-gradient(180deg, #0b1220 0%, #111a2e 220px, #f0f4fb 220px)',
      }}
    >
      <Header
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'transparent',
          height: 88,
          padding: '0 28px',
        }}
      >
        <Space size={14}>
          <div
            style={{
              width: 40,
              height: 40,
              borderRadius: 10,
              display: 'grid',
              placeItems: 'center',
              background: 'linear-gradient(135deg, #1677ff 0%, #36cfc9 100%)',
              boxShadow: '0 8px 20px rgba(22,119,255,0.35)',
            }}
          >
            <RadarChartOutlined style={{ color: '#fff', fontSize: 20 }} />
          </div>
          <div>
            <Title level={4} style={{ color: '#fff', margin: 0 }}>
              招标商机挖掘系统
            </Title>
            <Text style={{ color: 'rgba(255,255,255,0.75)' }}>数据看板模式</Text>
          </div>
        </Space>
        <Tag color="blue" style={{ borderRadius: 999, padding: '4px 10px' }}>
          MVP
        </Tag>
      </Header>
      <div style={{ padding: '0 28px' }}>
        <Menu
          mode="horizontal"
          selectedKeys={[location.pathname]}
          items={menuItems}
          style={{
            border: 'none',
            borderRadius: 12,
            padding: '0 8px',
            boxShadow: '0 10px 24px rgba(8, 20, 45, 0.15)',
          }}
        />
      </div>
      <Content style={{ padding: '20px 28px 28px' }}>
        <Routes>
          <Route path="/" element={<TenderList />} />
          <Route path="/company" element={<CompanyProfile />} />
        </Routes>
      </Content>
    </Layout>
  )
}

export default App
