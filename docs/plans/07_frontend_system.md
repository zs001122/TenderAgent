# 前端系统规划

## 概述

本文档描述招标商机挖掘系统的前端实现规划，基于 Vite + React + TypeScript + Ant Design 技术栈。

## 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Vite | 8.x | 构建工具 |
| React | 19.x | UI 框架 |
| TypeScript | 5.x | 类型系统 |
| Ant Design | 6.x | UI 组件库 |
| Axios | 1.x | HTTP 客户端 |
| React Router | 7.x | 路由管理 |

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
- Ranking 评分详情：总分、等级、各维度得分、维度权重和说明
- 匹配证据：Gate 证据、资料证据命中、缺失项、风险/复核项
- Agent 决策建议：行动、置信度、理由、风险点

### 3. 公司画像配置页面

**路径**: `/company`

**当前实现**:
- 页面已从单一配置表单升级为资料管理工作台。
- 顶部展示资料库概览。
- 使用 Tabs 分区：资料导入、资料库、匹配策略、校验问题。

**匹配策略配置**:
- 公司名称配置
- 目标领域选择（多选）
- 预算范围配置（最小值-最大值）
- 资质证书配置（多选+可输入）
- 服务区域配置（多选）
- 保存和重置功能

**资料导入**:
- 上传 `.xlsx` 文件并先预览。
- 展示解析资料数、有效资质数、过期数、校验提示和样例资料。
- 用户确认后才写入资料库。

**资料库维护**:
- 分页展示结构化资料。
- 支持资料类型、状态、来源 Sheet、关键词筛选。
- 支持新增、编辑、停用、恢复资料。
- 支持显示已停用资料。
- 详情抽屉展示来源类型、证书/合同字段、关键词和原始 JSON。

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
| POST | /api/company/import-excel/preview | Excel 解析预览 |
| POST | /api/company/import-excel | 确认导入 Excel 资料 |
| GET | /api/company/assets | 分页查询资料库 |
| GET | /api/company/assets/summary | 获取资料库摘要 |
| POST | /api/company/assets | 新增资料 |
| PUT | /api/company/assets/{asset_id} | 编辑资料 |
| DELETE | /api/company/assets/{asset_id} | 停用资料 |
| POST | /api/company/assets/{asset_id}/restore | 恢复资料 |
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
   - 当前 Vite build 仍提示主 chunk 超过 500 kB

2. **功能增强**
   - 高级筛选和搜索
   - 数据可视化图表
   - 导出功能
   - 公司资料导入历史和回滚
   - Excel 模板说明或模板下载

3. **用户体验**
   - 移动端适配
   - 暗黑模式
   - 国际化

4. **测试**
   - 公司资料工作台关键交互 E2E
   - 分析详情匹配证据 Tab E2E
