# Project AI Instructions: zcode-sync

- `D:\program_files\` 为用户的核心软件安装/运行存放目录。
- **便携版更新与覆盖边界**：
  - 每次构建或发布 `zcode-sync` 的新版本便携版时，自动复制最新可执行程序至 `D:\program_files\zcode_sync\`；
  - **允许覆盖**：仅限程序本身的可执行二进制文件 (`zcode-sync.exe`) 及程序运行依赖资产；
  - **严格保留**：用户配置文件（如 `config.json`、`provider_config.json` 等）、本地数据库、历史备份（`.bak`）以及用户个人产生的所有数据，严禁覆盖或删除。
