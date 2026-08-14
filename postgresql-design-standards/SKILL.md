---
name: postgresql-design-standards
description: Use when designing PostgreSQL database schemas, creating tables, writing migrations or ALTER TABLE on large tables, or reviewing database code. Triggers on keywords like CREATE TABLE, schema design, foreign key, naming convention, UUID, SERIAL, Identity, constraint naming, NOT VALID, CREATE INDEX CONCURRENTLY, pagination, 数据库设计, 表结构, 命名规范, 迁移.
---

# PostgreSQL 数据库设计规范

团队数据库设计标准，适用于 PostgreSQL 18+（`uuidv7()`、`NOT NULL ... NOT VALID`、虚拟生成列均为 PG 18 特性）。

## 快速参考

### 命名规范

| 元素 | 格式 | 示例 |
|------|------|------|
| 表名 | snake_case，复数 | `users`, `order_items` |
| 列名 | snake_case | `created_at`, `user_id` |
| 主键 | `id` | `id UUID` |
| 外键字段 | `{实体}_id` | `class_id`, `parent_id`（自关联） |
| 普通索引 | `idx_{表名}_{列名}` | `idx_users_email` |
| 唯一索引/唯一约束 | `uni_{表名}_{描述}` | `uni_users_email_active` |
| 主键约束 | `pk_{表名}` | `pk_users` |
| 检查约束 | `chk_{表名}_{描述}` | `chk_users_status` |
| 外键约束 | `fk_{表名}_{列名}` | `fk_tasks_class_id` |
| NOT NULL 约束（仅迁移显式命名时） | `nn_{表名}_{列名}` | `nn_orders_customer_id` |
| 触发器 | `trg_{表名}_{用途}` | `trg_users_updated_at` |

> 列内联的 NOT NULL 不命名；只有大表迁移走 `NOT VALID` 流程时才显式命名（见「大表迁移安全」）。

### 数据类型选择

| 使用场景 | 推荐 | 避免 |
|----------|------|------|
| 主键（业务表） | `UUID` + `uuidv7()` | `SERIAL`, `gen_random_uuid()` |
| 主键（静态表） | `BIGINT Identity` | `SERIAL` |
| 时间戳 | `TIMESTAMPTZ` | `TIMESTAMP` |
| 字符串 | `TEXT`（需限长时加 `CHECK (char_length(col) <= N)`） | `VARCHAR(N)` |
| 枚举类字段 | `TEXT` + `CHECK` | 原生 `ENUM`（改值需 DDL，难维护） |
| JSON | `JSONB` | `JSON` |
| 金额 | `NUMERIC(19,4)` | `FLOAT` |
| 派生值（拼接/JSONB 提取） | 生成列（PG18 默认 VIRTUAL） | 应用层冗余字段 |

> **为什么用 UUIDv7？** UUIDv4（`gen_random_uuid()`）完全随机，会导致 B-Tree 索引页分裂和碎片化。UUIDv7 时间有序，写入性能接近自增 ID。
>
> **UUIDv7 的隐私代价**：前 48 位是毫秒时间戳，`uuid_extract_timestamp()` 可直接还原记录创建时间；对外暴露的 v7 ID 序列还能被用来估算业务量。创建时间/单量属于敏感信息时，不要把 v7 主键直接暴露。

### 主键类型策略

| 场景 | 类型 |
|------|------|
| 分布式/多写入点 | UUIDv7 |
| ID 暴露在 URL/API，创建时间不敏感 | UUIDv7 |
| ID 暴露在 URL/API，创建时间/单量敏感 | 内部主键 UUIDv7 + 对外另设 UUIDv4（或不透明短码）唯一字段 |
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

何时应提议升 L2（满足多条时在评审中提出）：
- 数据错误代价极高（资金、权限、计费）
- 写入频率低、无分库分表计划
- 多个写入方绕过统一应用层（脚本、ETL 直写）

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
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    parent_id UUID NOT NULL,  -- L1 逻辑外键

    -- 时间戳
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- 约束（前缀命名，PK 也在此统一管理）
    CONSTRAINT pk_table_name PRIMARY KEY (id),
    CONSTRAINT chk_table_name_status CHECK (status IN ('active', 'inactive'))
);

-- 必须：为外键字段创建索引
CREATE INDEX idx_table_name_parent_id ON table_name(parent_id);

-- 必须：为核心表和字段添加注释
COMMENT ON TABLE table_name IS '表的业务说明';
COMMENT ON COLUMN table_name.status IS '状态: active, inactive';

-- 必须：updated_at 自动更新触发器（WHEN 守卫避免空更新也刷新时间戳）
CREATE TRIGGER trg_table_name_updated_at
    BEFORE UPDATE ON table_name
    FOR EACH ROW
    WHEN (OLD.* IS DISTINCT FROM NEW.*)
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

### 多列索引与 skip scan（PG18）

PG18 的 B-tree skip scan 让查询缺少前导列条件时也能用上多列索引（前导列基数低时效果好）。设计含低基数列（如 `status`、`tenant_id`）的多列索引时，把低基数列放前导位可提高索引复用率，减少单列冗余索引。

### 唯一约束的三个坑

```sql
-- 坑 1：软删除 + 普通 UNIQUE —— 已删除的记录会阻止新记录
-- 坑 2：email 直接唯一 —— Foo@x.com 与 foo@x.com 并存
-- 正确：函数部分唯一索引，只约束未删除记录，且大小写归一
CREATE UNIQUE INDEX uni_users_email_active
ON users (lower(email))
WHERE deleted_at IS NULL;

-- 坑 3：含可空列的唯一约束 —— 多个 NULL 默认互不冲突
-- 需要"NULL 也唯一"时（PG15+）：
CREATE UNIQUE INDEX uni_configs_key ON configs (tenant_id, key) NULLS NOT DISTINCT;
```

> UNIQUE 约束/唯一索引本身就是 B-Tree 索引，可直接支撑等值查询——**不要**再为同一列建普通 `idx_` 索引（包括"外键字段必须建索引"规则：该字段已有唯一索引时即视为已满足）。

### 时间区间不重叠（PG18）

"同一资源同一时段不可重复"（排课、预约、价格生效区间）用 temporal 约束，不要在应用层查重：

```sql
CONSTRAINT uni_bookings_room_period UNIQUE (room_id, period WITHOUT OVERLAPS)
-- period 为 tstzrange 列；需先 CREATE EXTENSION btree_gist
```

## 大表迁移安全

大表（千万行以上）的 DDL 必须评估锁级别，禁止长时间持有 `ACCESS EXCLUSIVE` 锁。

### 加 NOT NULL（PG18 原生两步法）

```sql
-- 直接 SET NOT NULL 会锁表全扫。PG18 起用 NOT VALID 拆两步：
-- 步骤 1：秒级完成，只改目录，新写入立即受约束
ALTER TABLE orders ADD CONSTRAINT nn_orders_customer_id NOT NULL customer_id NOT VALID;
-- 步骤 2：校验存量数据，只持 SHARE UPDATE EXCLUSIVE 锁，不阻塞读写
ALTER TABLE orders VALIDATE CONSTRAINT nn_orders_customer_id;
```

> PG18 之前的等价写法是 `CHECK (col IS NOT NULL) NOT VALID` → `VALIDATE` → `SET NOT NULL` → 删 CHECK 四步；PG18 上一律用原生两步法。

### 在线建索引

```sql
-- CONCURRENTLY 不阻塞写入；不能放在事务块内
CREATE INDEX CONCURRENTLY idx_orders_customer_id ON orders (customer_id);
-- 失败会残留 INVALID 索引：先 DROP INDEX CONCURRENTLY 再重试
```

### 其他规则

- 加 FK/CHECK 约束同样用 `NOT VALID` + `VALIDATE CONSTRAINT` 两步
- 加列带默认值是安全的（PG11+ 不重写表）；但改列类型多数会重写全表，需走"新列 + 双写 + 回填 + 切换"
- 迁移脚本设置 `lock_timeout`（如 `5s`），拿不到锁快速失败重试，避免排队阻塞后续所有查询

## 生成列（PG18）

派生值优先用生成列而非应用层冗余维护：

```sql
-- VIRTUAL（PG18 默认）：读时计算，不占存储，不可建索引
display_name TEXT GENERATED ALWAYS AS (first_name || ' ' || last_name),
-- 需要索引/高频读时用 STORED
email_domain TEXT GENERATED ALWAYS AS (split_part(email, '@', 2)) STORED
```

## 反模式（禁止）

| 反模式 | 问题 | 正确做法 |
|--------|------|----------|
| `SELECT *`（原生 SQL） | 无法 Index Only Scan，表结构变更风险 | 明确列出所需字段；ORM 默认加载全字段可接受，仅在性能热点处用 `load_only()` 优化 |
| 不带 `LIMIT` 的列表查询 | 可能返回百万行撑爆内存 | 始终加 LIMIT |
| 大 `OFFSET` 深分页 | OFFSET 10000 仍要扫描并丢弃 1 万行 | keyset 分页：`WHERE (created_at, id) < (?, ?) ORDER BY created_at DESC, id DESC LIMIT ?` |
| 在数据库做复杂字符串拼接 | CPU 密集，阻塞连接 | 移至应用层；确属派生值用生成列 |
| `ON DELETE CASCADE` | 级联删除难以追踪，易误删 | 使用 `RESTRICT` + 应用层处理 |
| UUIDv4 作为高频写入大表主键 | 索引碎片化，写入性能下降 | 使用 UUIDv7 |
| 对外暴露 UUIDv7 且创建时间敏感 | 时间戳可被提取，泄露业务量 | 对外另设 UUIDv4/不透明 ID |
| 软删除表用普通 UNIQUE | 已删除记录阻止新记录 | 部分索引 `WHERE deleted_at IS NULL` |
| 大表直接 `SET NOT NULL` / 普通 `CREATE INDEX` | 长时间锁表 | `NOT VALID` 两步法 / `CONCURRENTLY` |

## 检查清单

新建表：
- [ ] 表名：复数、snake_case
- [ ] 主键：UUIDv7（业务表）或 Identity（静态表）；对外暴露且时间敏感时内外 ID 分离
- [ ] 约束：前缀命名（pk_, uni_, chk_, nn_）
- [ ] 外键字段：`{实体}_id` + 索引
- [ ] 默认 L1（无 FK 约束）
- [ ] TIMESTAMPTZ 而非 TIMESTAMP；TEXT 而非 VARCHAR；JSONB 而非 JSON
- [ ] 唯一约束：考虑软删除（部分索引）、大小写（`lower()`）、NULL 语义（`NULLS NOT DISTINCT`）
- [ ] updated_at 触发器（带 WHEN 守卫）
- [ ] 核心表/字段添加 COMMENT

迁移（大表）：
- [ ] NOT NULL / FK / CHECK 用 `NOT VALID` + `VALIDATE` 两步
- [ ] 索引用 `CREATE INDEX CONCURRENTLY`（事务块外）
- [ ] 设置 `lock_timeout`
- [ ] 改列类型评估是否重写全表

应用层：
- [ ] 插入前验证父记录存在
- [ ] 处理孤儿数据清理
- [ ] 幂等设计
- [ ] 原生 SQL 禁止 SELECT *；ORM 默认加载可接受，性能热点处优化
- [ ] 列表查询必须有 LIMIT；深分页用 keyset
