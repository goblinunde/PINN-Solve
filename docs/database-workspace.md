# 数据库工作台说明

数据库工作台是当前前端新增的一个操作页，目标是让你直接在 Web 界面中完成 MySQL 连接、建库、建表、数据录入和 CSV 导入，而不必每次切回命令行或第三方客户端。

## 1. 主要能力

当前已支持:

- 保存 MySQL 连接配置
- 测试连接
- 读取数据库和表
- 创建数据库
- 创建表
- 插入 JSON 行数据
- 粘贴 CSV 内容并导入
- 本地 MySQL 直连
- SSH 隧道连接云端 SQL 服务

当前尚未完整支持:

- 删除数据库
- 删除表
- 修改表结构
- 行级更新和删除
- 非 MySQL 方言适配

## 2. 访问入口

前端导航栏中有数据库工作台入口，对应页面文件:

- `frontend/src/views/DatabaseView.vue`

后端 API 前缀:

- `/api/db`

## 3. 本地 MySQL 连接步骤

### 先确保 MySQL 已启动

例如在 Linux 上:

```bash
sudo systemctl start mysqld
```

### 创建业务数据库

进入 MySQL:

```bash
mysql -u root -p
```

然后执行:

```sql
CREATE DATABASE PINNSOLVER CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
SHOW DATABASES;
```

### 前端填写连接信息

建议填写:

- `Connection Name`: `本地 PINNSOLVER`
- `Host`: `127.0.0.1`
- `Port`: `3306`
- `User Name`: `root`
- `Password`: 你的 MySQL root 密码
- `Database`: `PINNSOLVER`

如果想保存密码，勾选 `Save password`。

## 4. SSH 云端 SQL 连接步骤

如果你的 MySQL 不在本机，而是在云服务器上，可以使用 `Use SSH tunnel for cloud SQL service`。

需要填写:

- `SSH Host`
- `SSH Port`
- `SSH User`
- `SSH Password`

或者使用私钥路径:

- `SSH Key Path`

典型场景:

- MySQL 仅监听云主机内网地址
- 安全组不对公网开放 3306
- 需要先 SSH 到跳板机或业务机再转发到 MySQL

## 5. 建表建议

当前前端建表是基于字段列表的简单模式，适合先落一批训练样本或测试样本。

例如创建训练样本表:

- `id` `INT AUTO_INCREMENT`
- `split` `VARCHAR(16)`
- `x` `DOUBLE`
- `t` `DOUBLE`
- `target` `DOUBLE`

如果需要主键，勾选 `主键`。如果允许空值，勾选 `可空`。

## 6. JSON 行数据导入

JSON 行数据适合快速录入少量样本。格式示例:

```json
[
  { "split": "train", "x": 0.1, "t": 0.0, "target": 0.52 },
  { "split": "train", "x": 0.2, "t": 0.0, "target": 0.49 },
  { "split": "test", "x": 0.3, "t": 0.1, "target": 0.44 }
]
```

录入流程:

1. 选择目标数据库
2. 填写目标表名
3. 在 JSON 编辑框中粘贴数据
4. 点击“写入表数据”

## 7. CSV 导入

CSV 适合导入成批样本。推荐第一行为表头，例如:

```csv
split,x,t,target
train,0.1,0.0,0.52
train,0.2,0.0,0.49
test,0.3,0.1,0.44
```

导入前建议先确保:

- 目标数据库已存在
- 目标表已存在
- 列名与 CSV 表头一致

## 8. 安全说明

当你勾选 `Save password` 时，系统会尝试将以下敏感信息加密后存储:

- MySQL 登录密码
- SSH 登录密码
- SSH 私钥口令

当前安全策略:

- 加密过程由 Rust 层负责
- 前端不会重新显示明文密码
- 后端只在测试连接或执行数据库操作时临时解密

## 9. 常见错误

### `/api/db/profiles` 返回 404

说明运行中的后端仍是旧版本，重启 API 即可。

### `No module named 'pymysql'`

说明后端环境缺少 MySQL 驱动，执行:

```bash
cd backend
./install-deps.sh cpu
```

### 保存连接时报认证失败

优先检查:

- 用户名是否正确
- 密码是否正确
- `Host` 是否填成了 `127.0.0.1`
- 目标数据库是否已经创建

### SSH 隧道模式无法连接

优先检查:

- SSH 用户是否有登录权限
- 私钥路径是否存在于后端运行机器
- 云服务器安全组是否允许 SSH 端口访问

## 10. 推荐实践

- 本地开发使用一个固定数据库，如 `PINNSOLVER`
- 训练样本与测试样本建议用 `split` 字段区分
- 大规模导入优先使用 CSV
- 先用数据库工作台完成结构管理，再逐步接入训练流
