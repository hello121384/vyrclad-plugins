# Vyrclad 插件仓库

所有共享插件以完整 ZIP 放在 [packages](packages)。仓库按文件名识别插件和版本，包里可以放多个文件和目录。

1. 将插件文件压缩为 `插件ID@版本.zip`，例如 `team.inventory@1.2.0.zip`。ID 使用小写字母开头，可含数字、点、下划线和连字符。版本使用三段数字。普通文件包无须清单，单个 ZIP 上限为 32 MiB。
2. 在 GitHub 的 `packages/` 打开 **Add file → Upload files**，上传 ZIP 并合入默认分支。Actions 会更新版本索引。更新插件时使用新的版本号。
3. 在 Vyrclad 工作台打开「插件管理 → GitHub 仓库」，输入本仓库地址，点「检查更新」并选择版本。也可以把同一个 ZIP 直接上传到工作台。两条路径使用整包的 SHA-256，支持下载原包。

索引工作流需要向默认分支写入 `vyrclad-index.json` 的权限。仓库策略要求走拉取请求时，可以运行 `python build_index.py`，将 ZIP 和生成的索引一并提交评审。

| 插件 | 版本 | 处理结果 |
| --- | --- | --- |
| [team.inventory](packages/team.inventory@1.2.0.zip) | 1.2.0 | 按服务编号归并 CSV 记录，保留服务名称、负责人和原始编号，内含两份示例清单。 |
| [vyrclad.compose-services](packages/vyrclad.compose-services@1.1.0.zip) | 1.1.0 | 读取 Compose 清单中声明的服务及镜像。 |
