---
name: api-design-principles
description: Use when designing REST APIs, reviewing API endpoints, or establishing API conventions for a project. Triggers on keywords like REST, API design, endpoint, HTTP methods, status codes, pagination, versioning.
---

# API Design Principles

RESTful API 设计通用原则（语言无关）。

> **本规范是 API 设计总纲。** 所有框架级实现规范（如 `api-design-fastapi`、`api-design-gin` 等）必须遵循本文档中的 URL 设计、HTTP 方法/状态码、错误格式、分页、响应约定等规则。框架 skill 只能在本总纲基础上做语言/框架特定的补充，不得覆盖或违反总纲规则。
>
> **已有实现规范：**
> - `api-design-fastapi` — Python FastAPI 实现

## URL 设计

### 命名规范

| 规则 | 正确 | 错误 |
|------|------|------|
| 使用名词复数 | `/users`, `/orders` | `/user`, `/getOrders` |
| 小写 + 连字符 | `/user-profiles` | `/userProfiles`, `/user_profiles` |
| 资源层级 | `/users/{id}/orders` | `/getUserOrders` |
| CRUD 避免动词 | `POST /orders` | `POST /createOrder` |

### 嵌套资源

**最多一层嵌套**，更深的用 query param 或顶层资源：

```
# 正确：一层嵌套
GET /api/v1/classes/{classId}/tasks

# 错误：两层以上嵌套
GET /api/v1/classes/{classId}/tasks/{taskId}/progress

# 正确：拍平为顶层资源 + query param
GET /api/v1/task-progress?taskId=xxx
```

### 非 CRUD 动作端点

CRUD 操作用名词（`POST /orders` = 创建订单），但**非 CRUD 的业务动作允许使用动词**：

```
POST /api/v1/classes/{classId}/join       # 加入班级
POST /api/v1/classes/{classId}/archive    # 归档班级
POST /api/v1/sync/push                    # 上行同步
GET  /api/v1/sync/pull                    # 下行同步
```

**判断标准：**
- 能自然建模为资源 CRUD → 用名词（`POST /class-memberships` 适合管理员批量管理成员）
- 表达用户意图/动作 → 用动词（`/join` 比 `/class-memberships` 更直觉）
- 业界惯例：GitHub `/merges`、Stripe `/capture`、Slack `/invite`

### 版本策略

**推荐：URI Path**（除非有特殊需求）

```
/api/v1/users
/api/v2/users
```

理由：简单直观、调试方便、业界主流（GitHub、Stripe、Twitter）

**其他方案**（特殊场景）：
- Query String: `/api/users?version=1`
- Header: `Api-Version: 1` 或 `Accept: application/vnd.api.v1+json`

## HTTP 方法

| 方法 | 用途 | 幂等 | 安全 |
|------|------|------|------|
| GET | 获取资源 | ✓ | ✓ |
| POST | 创建资源 | ✗ | ✗ |
| PUT | 全量更新 | ✓ | ✗ |
| PATCH | 部分更新 | ✗ | ✗ |
| DELETE | 删除资源 | ✓ | ✗ |

## HTTP 状态码

### 成功

| 码 | 场景 |
|----|------|
| 200 | GET/PUT/PATCH 成功 |
| 201 | POST 创建成功 |
| 204 | DELETE 成功（无返回体） |

### 客户端错误

| 码 | 场景 |
|----|------|
| 400 | 请求格式错误、参数校验失败 |
| 401 | 未认证（需要登录） |
| 403 | 已认证但无权限 |
| 404 | 资源不存在 |
| 409 | 冲突（如重复创建） |
| 422 | 请求格式正确但语义错误 |

### 服务端错误

| 码 | 场景 |
|----|------|
| 500 | 服务器内部错误 |
| 502 | 网关错误 |
| 503 | 服务不可用 |

## 错误响应格式

```json
{
  "error": {
    "code": "validation_error",
    "message": "邮箱格式不正确",
    "details": [
      {"field": "email", "message": "必须是有效的邮箱地址"}
    ]
  }
}
```

**错误码风格**：`snake_case`（业界主流：Stripe、GitHub、Slack）

**原则**：
- 统一格式，前端易处理
- `code` 用于程序判断（小写下划线）
- `message` 用于展示给用户
- `details` 用于字段级错误

## API 字段命名策略

**原则：各语言遵循自身惯例，API 输出统一 camelCase。**

| 层 | 命名风格 | 示例 |
|----|---------|------|
| 数据库列名 | snake_case | `created_at`, `class_id` |
| Python/Rust 代码 | snake_case | `created_at`, `class_id` |
| Go/Java/Swift 代码 | camelCase | `createdAt`, `classId` |
| **API 请求/响应 JSON** | **camelCase** | `createdAt`, `classId` |
| URL query param | camelCase | `?pageSize=20&classId=xxx` |
| 错误码 (`error.code`) | snake_case | `validation_error`（例外：错误码是机器标识符，不是字段） |

**实现方式（以 Python/Pydantic 为例）：**
```python
model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
```

## 分页

### 推荐：游标分页（大数据量）

```
GET /api/v1/users?cursor=abc123&limit=20

{
  "data": [...],
  "pagination": {
    "nextCursor": "xyz789",
    "hasMore": true
  }
}
```

### 简单场景：偏移分页

```
GET /api/v1/users?page=2&pageSize=20

{
  "data": [...],
  "pagination": {
    "total": 100,
    "page": 2,
    "pageSize": 20,
    "totalPages": 5
  }
}
```

## 请求/响应约定

### 请求体

- Content-Type: `application/json`
- 字段命名：camelCase（见"API 字段命名策略"）

### 响应体

- 单资源：直接返回对象
- 列表：包装在 `data` 数组中
- 时间格式：ISO 8601（`2024-01-15T10:30:00Z`）

## Quick Reference

```
# CRUD 资源操作
GET    /api/v1/users              # 列表
POST   /api/v1/users              # 创建
GET    /api/v1/users/{id}         # 详情
PUT    /api/v1/users/{id}         # 全量更新
PATCH  /api/v1/users/{id}         # 部分更新
DELETE /api/v1/users/{id}         # 删除

# 一层嵌套资源
GET    /api/v1/users/{id}/orders  # 嵌套资源

# 非 CRUD 动作
POST   /api/v1/classes/{id}/join  # 业务动作用动词
```
