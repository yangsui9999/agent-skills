---
name: postgresql-design-standards
description: Use when designing PostgreSQL database schemas, creating tables, writing migrations, or reviewing database code. Triggers on keywords like CREATE TABLE, schema design, foreign key, naming convention, UUID, SERIAL, Identity, constraint naming, 数据库设计, 表结构, 命名规范.
---

# PostgreSQL 数据库设计规范

团队数据库设计标准，适用于 PostgreSQL 18+（`uuidv7()` 为 PG 18 原生内置函数）。

## 快速参考

### 命名规范

| 元素 | 格式 | 示例 |
|------|------|------|
| 表名 | snake_case，复数 | `users`, `order_items` |
| 列名 | snake_case | `created_at`, `user_id` |
| 主键 | `id` | `id UUID` |
| 外键字段 | `{实体}_id` | `class_id`, `parent_id`（自关联） |
| 索引 | `idx_{表名}_{列名}` | `idx_users_email` |
| 主键约束 | `pk_{表名}` | `pk_users` |
| 唯一约束 | `uni_{表名}_{列名}` | `uni_users_email` |
| 检查约束 | `chk_{表名}_{描述}` | `chk_users_role` |
| 外键约束 | `fk_{表名}_{列名}` | `fk_tasks_class_id` |

### 数据类型选择

| 使用场景 | 推荐 | 避免 |
|----------|------|------|
| 主键（业务表） | `UUID` + `uuidv7()` | `SERIAL`, `gen_random_uuid()` |
| 主键（静态表） | `BIGINT Identity` | `SERIAL` |
| 时间戳 | `TIMESTAMPTZ` | `TIMESTAMP` |
| 字符串（无限制） | `TEXT` | `VARCHAR` |
| JSON | `JSONB` | `JSON` |
| 金额 | `NUMERIC(19,4)` | `FLOAT` |

> **为什么用 UUIDv7？** UUIDv4（`gen_random_uuid()`）完全随机，会导致 B-Tree 索引页分裂和碎片化。UUIDv7 时间有序，写入性能接近自增 ID。

### 主键类型策略

| 场景 | 类型 |
|------|------|
| 分布式/多写入点 | UUIDv7 |
| ID 暴露在 URL/API | UUID |
| 大表、性能敏感 | BIGINT Identity |
| 单库、可读性优先 | BIGINT Identity |

### 外键策略（L1/L2）

**默认：L1 逻辑外键**
- 保留 `{实体}_id` 字段
- **必须**创建索引
- **不创建** FK 约束
- 应用层保证一致性

```sql
-- L1 示例（默认）
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuidv7(),
    class_id UUID NOT NULL,  -- L1：无 FK 约束
    ...
);
CREATE INDEX idx_tasks_class_id ON tasks(class_id);
```

**例外：L2 物理外键**（需团队评审）
- 同库、同 schema、结构稳定
- 使用 `ON DELETE RESTRICT`（禁止 CASCADE）

```sql
-- L2 示例（需评审）
CONSTRAINT fk_class_members_class_id
    FOREIGN KEY (class_id) REFERENCES classes(id)
    ON DELETE RESTRICT
```

## 建表模板

```sql
CREATE TABLE table_name (
    id UUID NOT NULL DEFAULT uuidv7(),

    -- 业务字段
    name VARCHAR(100) NOT NULL,
    parent_id UUID NOT NULL,  -- L1 逻辑外键

    -- 时间戳
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- 约束（前缀命名，PK 也在此统一管理）
    CONSTRAINT pk_table_name PRIMARY KEY (id),
    CONSTRAINT uni_table_name_field UNIQUE (field),
    CONSTRAINT chk_table_name_status CHECK (status IN ('a', 'b'))
);

-- 必须：为外键字段创建索引
CREATE INDEX idx_table_name_parent_id ON table_name(parent_id);

-- 必须：为核心表和字段添加注释
COMMENT ON TABLE table_name IS '表的业务说明';
COMMENT ON COLUMN table_name.status IS '状态: active, inactive';

-- 必须：updated_at 自动更新触发器
CREATE TRIGGER trg_table_name_updated_at
    BEFORE UPDATE ON table_name
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

### updated_at 通用触发器函数

```sql
-- 在数据库中只需创建一次，所有表复用
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

> **注意**：PostgreSQL 没有 MySQL 的 `ON UPDATE CURRENT_TIMESTAMP`，必须用触发器实现。

## Identity vs SERIAL

```sql
-- 避免（旧语法）
id SERIAL PRIMARY KEY

-- 推荐（SQL 标准）
id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY
```

## 索引策略

### 覆盖索引（Index Only Scan）

```sql
-- 使用 INCLUDE 避免回表查询
CREATE INDEX idx_tasks_class_status
ON tasks(class_id, status)
INCLUDE (id, created_at);
```

### 软删除场景的唯一约束

```sql
-- 错误：已删除的记录会阻止新记录
CREATE UNIQUE INDEX idx_users_email ON users(email);

-- 正确：部分索引，只约束未删除的记录
CREATE UNIQUE INDEX uni_users_email_active
ON users(email)
WHERE deleted_at IS NULL;
```

## 反模式（禁止）

| 反模式 | 问题 | 正确做法 |
|--------|------|----------|
| `SELECT *`（原生 SQL） | 无法 Index Only Scan，表结构变更风险 | 明确列出所需字段；ORM 默认加载全字段可接受，仅在性能热点处用 `load_only()` 优化 |
| 不带 `LIMIT` 的列表查询 | 可能返回百万行撑爆内存 | 始终加 LIMIT |
| 在数据库做复杂字符串拼接 | CPU 密集，阻塞连接 | 移至应用层 |
| `ON DELETE CASCADE` | 级联删除难以追踪，易误删 | 使用 `RESTRICT` + 应用层处理 |
| UUIDv4 作为高频写入大表主键 | 索引碎片化，写入性能下降 | 使用 UUIDv7 |
| 软删除表用普通 UNIQUE | 已删除记录阻止新记录 | 部分索引 `WHERE deleted_at IS NULL` |

## 检查清单

新建表：
- [ ] 表名：复数、snake_case
- [ ] 主键：UUIDv7（业务表）或 Identity（静态表）
- [ ] 约束：前缀命名（pk_, uni_, chk_）
- [ ] 外键字段：`{实体}_id` + 索引
- [ ] 默认 L1（无 FK 约束）
- [ ] TIMESTAMPTZ 而非 TIMESTAMP
- [ ] JSONB 而非 JSON
- [ ] updated_at 触发器
- [ ] 核心表/字段添加 COMMENT

应用层：
- [ ] 插入前验证父记录存在
- [ ] 处理孤儿数据清理
- [ ] 幂等设计
- [ ] 原生 SQL 禁止 SELECT *；ORM 默认加载可接受，性能热点处优化
- [ ] 列表查询必须有 LIMIT
