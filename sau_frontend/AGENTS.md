# SAU_FRONTEND — Vue 3 前端

独立 Vue 子项目，配合 `sau_backend.py` Flask 后端使用。

## STRUCTURE

```
sau_frontend/
├── src/
│   ├── main.js             # Vue 入口（App + Router + Pinia + ElementPlus）
│   ├── App.vue             # 根组件
│   ├── router/index.js     # 路由（WebHash 模式，5 个页面）
│   ├── views/              # 页面组件
│   │   ├── Dashboard.vue
│   │   ├── AccountManagement.vue
│   │   ├── MaterialManagement.vue
│   │   ├── PublishCenter.vue
│   │   └── About.vue
│   ├── stores/             # Pinia 状态管理（account/user/app）
│   ├── api/                # API 请求封装（account/material/user）
│   ├── styles/             # SCSS 样式
│   └── utils/request.js    # Axios 封装（http 对象）
├── vite.config.js          # 构建配置（API 代理到 :5409）
└── package.json
```

## CONVENTIONS

- **Vue 3 + Vite + Element Plus + Pinia + Sass**
- **组件语法**：`<script setup>`
- **路由**：`createWebHashHistory()`，不用 HTML5 History
- **HTTP**：通过 `src/utils/request.js` 的 `http` 对象，不直接 import axios
- **API 响应格式**：`{code: 200, success: true/false, msg/message: str}`
- **平台类型 ID**：1=小红书, 2=视频号, 3=抖音, 4=快手
- **构建**：`sourcemap: false`，手动分包（vue/vue-router/pinia | element-plus | axios）
- **开发代理**：`/api` → `http://localhost:5409`

## ANTI-PATTERNS

- ❌ 用 HTML5 History 路由
- ❌ 直接 `import axios from 'axios'` — 用 `src/utils/request.js`
- ❌ 在组件内硬编码 API URL — 走 `src/api/` 封装

## COMMANDS

```bash
npm install && npm run dev    # 开发 :5173
npm run build                 # 生产构建
```
