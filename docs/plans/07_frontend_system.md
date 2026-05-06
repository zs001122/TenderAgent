# 前端系统规划

## 概述

本文档描述招标商机挖掘系统的前端实现规划，基于 Vite + React + TypeScript + Ant Design 技术栈。

## 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Vite | 8.x | 构建工具 |
| React | 18.x | UI 框架 |
| TypeScript | 5.x | 类型系统 |
| Ant Design | 5.x | UI 组件库 |
| Axios | 1.x | HTTP 客户端 |
| React Router | 6.x | 路由管理 |

## 目录结构

```
frontend/
├── src/
│   ├── components/          # 公共组件
│   │   └── AnalysisDetailModal.tsx
│   ├── pages/               # 页面组件
│   │   ├── TenderList.tsx
│   │   └── CompanyProfile.tsx
│   ├── services/            # API 服务
│   │   ├── api.ts
│   │   ├── tender.ts
│   │   └── company.ts
│   ├── types/               # TypeScript 类型
│   │   ├── index.ts
│   │   ├── tender.ts
│   │   └── company.ts
│   ├── App.tsx              # 主应用组件
│   └── main.tsx             # 入口文件
├── vite.config.ts           # Vite 配置
├── package.json
└── tsconfig.json
```

## 页面设计

### 1. 招标列表页面

**路径**: `/`

**功能**:
- 展示招标列表（标题、预算、发布日期、匹配评分、推荐等级）
- 分页功能
- 查看详情按钮

**匹配评分颜色**:
- A 级: 绿色 (success)
- B 级: 蓝色 (processing)
- C 级: 橙色 (warning)
- D 级: 红色 (error)

### 2. 分析详情弹窗

**触发**: 点击"查看详情"按钮

**展示内容**:
- 提取信息：预算、截止日期、资质要求、标签、联系人
- Gate 检查结果：通过/未通过状态
- Ranking 评分详情：总分、等级、各维度得分
- Agent 决策建议：行动、置信度、理由、风险点

### 3. 公司画像配置页面

**路径**: `/company`

**功能**:
- 公司名称配置
- 目标领域选择（多选）
- 预算范围配置（最小值-最大值）
- 资质证书配置（多选+可输入）
- 服务区域配置（多选）
- 保存和重置功能

## API 接口

### 招标相关

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/tenders/ | 获取招标列表 |
| GET | /api/tenders/{id} | 获取招标详情 |
| POST | /api/tenders/{id}/analyze | 触发分析 |
| GET | /api/tenders/{id}/analysis | 获取分析结果 |

### 公司画像相关

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/company/ | 获取公司画像 |
| PUT | /api/company/ | 更新公司画像 |
| POST | /api/company/reset | 重置为默认配置 |

## 配置说明

### Vite 代理配置

```typescript
// vite.config.ts
export default defineConfig({
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

## 启动命令

```bash
# 开发模式
npm run dev

# 生产构建
npm run build

# 预览构建结果
npm run preview
```

## 后续优化

1. **性能优化**
   - 代码分割（React.lazy）
   - 虚拟列表（大数据量）

2. **功能增强**
   - 高级筛选和搜索
   - 数据可视化图表
   - 导出功能

3. **用户体验**
   - 移动端适配
   - 暗黑模式
   - 国际化
