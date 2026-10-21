# RepoList

整理好的越狱源合集，适合手机打开。支持搜索、分组批量复制，以及一键添加到 Sileo、Zebra、Irisin。

🌐 **在线访问**：[https://repolist.goforit.si](https://repolist.goforit.si)

源不一定多，够用就好，按需添加。

## 怎么添加源

| 包管理器 | 方法 |
| --- | --- |
| **Sileo** | 点“复制全部”，打开 Sileo → 软件源 → 点 ＋，会自动识别剪贴板里的全部地址 |
| **Irisin** | 点“Irisin 添加”，整组一次性加入 |
| **Zebra** | 复制后在添加源界面粘贴 |
| **Cydia** | 复制地址后逐个添加 |

> 在微信或 QQ 里打开时，跳转按钮可能无效，请点右上角选择在 Safari 中打开。

## 推荐新源

两种方式，任选其一：

- **不熟悉 GitHub**：到 [Issues](../../issues/new/choose) 选择“推荐新源”，按表格填写即可，维护者审核后会加进去。
- **熟悉 GitHub**：直接修改 `repos.json`，在对应分组里加一项，然后提交 Pull Request：

```json
{ "name": "某某源", "note": "代表插件或作者介绍", "url": "https://example.github.io/repo/" }
```

- `name`：源的名字，简短好认
- `note`：代表作或作者介绍，没有可以留空 `""`
- `url`：源地址，以 `/` 结尾

## 收录标准

- 源能正常访问，并且里面确实有插件。
- 有明确的作者或用途，不收录内容重复的镜像源。
- 长期失效的源会被自动标记并移除。

## 状态标识 

GitHub Actions 每天凌晨自动运行 `scripts/check_repos.py`，逐个检查源：

- **插件数量**：读取源的 Packages 索引统计。
- **更新时间**：只有出现新插件或版本号变化时才刷新。作者重新生成索引文件不算更新。一年以上没有变化的标为“可能停更”。
- **状态**：能正常读取为正常；访问失败为检测异常；连续三天失败才标为已失效。

## 关于与支持

- **作者**：[Junhong](https://mjh.im/)
- **个人源**：[apt.mjh.im](https://apt.mjh.im/)
- **赏杯咖啡**：[支付宝赞助支持](alipays://platformapi/startapp?saId=10000007&qrcode=https%3A%2F%2Fqr.alipay.com%2Ffkx180736inoxop5mkbqh83%3F_s%3Dweb-other&launchKey=c7f8d186-3e05-4668-a7eb-8cf336c2108f-1780370320745)

## License

[MIT](LICENSE) © 2026 Junhong
