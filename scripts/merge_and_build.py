import json
import re
from pathlib import Path
from urllib.parse import urlparse

def clean_text(s):
    if not s:
        return ""
    # remove unwanted emoji clutter or wrapping brackets
    s = s.strip().strip("（）()【】[]")
    s = re.sub(r"[\t\r\n]+", " ", s)
    s = re.sub(r" +", " ", s)
    return s.strip()

def build_merged():
    alive_data = json.load(open("scripts/alive_repos.json"))
    original_repos = json.load(open("repos.json"))

    # Map existing URLs and (host, path)
    existing_urls = set()
    existing_hp = set()
    for g in original_repos:
        for s in g["sources"]:
            u = s["url"]
            existing_urls.add(u)
            p = urlparse(u)
            existing_hp.add((p.netloc.replace("www.", "").lower(), p.path))

    # Known alias/mirrors/migrations to deduplicate
    alias_map = {
        "http://sutuplus.github.io/repo/": "https://apt.sutuplus.com/",
        "http://tigisoftware.com/cydia/": "http://tigisoftware.com/repo/",
        "https://www.yourepo.com/": "https://yourepo.com/",
        "https://repo.yttxcs.com/": "https://yttxcs.com/",
        "https://repo.chariz.io/": "https://repo.chariz.com/",
        "http://rpetri.ch/repo/": "https://rpetri.ch/repo/",
        "http://akusio.github.io/": "https://akusio.github.io/",
        "http://cokepokes.github.io/": "https://cokepokes.github.io/",
        "http://dcsyhi1998.github.io/": "https://dcsyhi1998.github.io/",
        "http://apt.sutuplus.com/": "https://apt.sutuplus.com/",
        "http://apt.25mao.com/": "https://apt.25mao.com/",
        "https://sparkdev.me/": "http://sparkdev.me/",
        "http://tigisoftware.com/cydia/": None, # already in repos as http://tigisoftware.com/repo/
    }

    # Group assignments for new items
    OFFICIAL_DOMAINS = {
        "apt.thebigboss.org", "havoc.app", "repo.chariz.com", "ellekit.space",
        "roothide.github.io", "apt.procurs.us", "repo.palera.in", "build.frida.re",
        "getzbra.com", "repo.cypwn.xyz", "apt.fouadraheb.com", "apt.alfhaily.me"
    }
    THEME_KEYWORDS = ["theme", "美化", "主题", "check0ver", "dada", "soda", "alo.works"]

    new_official = []
    new_community = []
    new_dev = []
    new_theme = []

    seen = set(existing_urls)
    seen_hp = set(existing_hp)

    for item in alive_data:
        raw_u = item["url"]
        u = alias_map.get(raw_u, raw_u)
        if not u:
            continue

        p = urlparse(u)
        hp = (p.netloc.replace("www.", "").lower(), p.path)
        if u in seen or hp in seen_hp:
            continue

        seen.add(u)
        seen_hp.add(hp)

        meta = item.get("meta", {})
        cust = clean_text(item.get("info", {}).get("custom_name", ""))
        label = clean_text(meta.get("label", ""))
        origin = clean_text(meta.get("origin", ""))
        desc = clean_text(meta.get("description", ""))

        # Determine best Name
        name = ""
        note = ""

        # Specific known mappings
        if "thebigboss.org" in u:
            name, note = "BigBoss", "大老板老牌经典基础源"
        elif "havoc.app" in u:
            name, note = "Havoc", "主流付费与知名插件软件源"
        elif "chariz.com" in u:
            name, note = "Chariz", "国外主流综合商业软件源"
        elif "ellekit.space" in u:
            name, note = "ElleKit", "无根越狱核心 Hook 注入框架官方源"
        elif "roothide.github.io" in u:
            name, note = "RootHide", "RootHide 隐蔽越狱与兼容层官方源"
        elif "apt.procurs.us" in u:
            name, note = "Procursus", "现代越狱基础工具包官方源"
        elif "palera.in" in u:
            name, note = "palera1n", "palera1n 越狱官方基础源"
        elif "frida.re" in u:
            name, note = "Frida", "动态插桩与安全分析工具官方源"
        elif "getzbra.com" in u:
            name, note = "Zebra 官方源", "斑马包管理器官方源"
        elif "cypwn.xyz" in u:
            name, note = "Cypwn", "经典越狱插件归档与社区源"
        elif "cokepokes.github.io" in u:
            name, note = "CokePokes", "AppStore++、CrashReporter 作者源"
        elif "rpetri.ch" in u:
            name, note = "rpetrich", "RocketBootstrap 等核心依赖作者源"
        elif "akusio.github.io" in u:
            name, note = "akusio", "MilkyWay 窗口多任务分屏插件作者源"
        elif "ichitaso.com" in u:
            name, note = "ichitaso", "OTADisabler 屏蔽更新、PowerSelector"
        elif "ryleyangus.com" in u:
            name, note = "Ryley Angus", "Liberty Lite 屏蔽越狱检测作者源"
        elif "c1d3r.com" in u:
            name, note = "c1d3r", "PullOver Pro 分屏悬浮窗插件作者源"
        elif "getdelta.co" in u:
            name, note = "Delta", "Flex 3 补丁制作工具作者源"
        elif "creaturecoding.com" in u:
            name, note = "CreatureCoding", "Shuffle、Fabric 等精品插件"
        elif "autotouch.net" in u:
            name, note = "AutoTouch", "AutoTouch 触动精灵自动化脚本官方源"
        elif "tinyapps.cn" in u:
            name, note = "Tinyapps", "Fake GPS Pro、360虚拟定位官方源"
        elif "niceios.com" in u:
            name, note = "NiceiOS", "NiceBarX、NiceCaller 等精品状态栏电话插件"
        elif "snailovet.com" in u:
            name, note = "蜗牛源", "微信助手等功能优化插件"
        elif "cydiabc.top" in u:
            name, note = "小苹果源", "国内知名常用插件源"
        elif "dumpapp.com" in u:
            name, note = "锤子软件源", "DumpApp 官方源"
        elif "trollstorex.github.io" in u:
            name, note = "巨魔源", "TrollStore 巨魔常用应用与插件"
        elif "sutuplus.com" in u:
            name, note = "苏兔源", "常用美化与汉化插件源"
        elif "byg.iosios.net" in u:
            name, note = "搬运工源", "搬运工精选插件源"
        elif "yttxcs.com" in u:
            name, note = "壹筒天下源", "常用实用插件源"
        elif "rootless.zq666.eu.org" in u:
            name, note = "真皮源", "Hello 系列无根插件"
        elif "wwg135.github.io" in u:
            name, note = "M哥源", "wwg135 自用插件分享"
        else:
            # General fallback deduction
            primary = cust or label or origin or p.netloc
            primary = primary.replace("™", "").replace("🇨🇳", "").replace("", "").strip()
            # Clean "xxx - YouRepo"
            primary = re.sub(r" - YouRepo.*", "", primary)
            primary = re.sub(r"作者源.*", "", primary)
            name = primary if primary else p.netloc

            if desc and desc != name and len(desc) < 40 and not desc.startswith("http"):
                note = desc
            elif cust and cust != name:
                note = cust
            else:
                note = ""

        entry = {"name": name, "note": note, "url": u}

        # Classify
        full_text = (name + " " + note + " " + u).lower()
        if p.netloc.lower() in OFFICIAL_DOMAINS:
            new_official.append(entry)
        elif any(k in full_text for k in THEME_KEYWORDS):
            new_theme.append(entry)
        elif any(k in full_text for k in ["源", "汉化", "搬运", "苹果", "巨魔", "微信", "定位", "脚本", "自用", "之家"]):
            new_community.append(entry)
        else:
            new_dev.append(entry)

    print(f"Classified new entries: Official={len(new_official)}, Community={len(new_community)}, Dev={len(new_dev)}, Theme={len(new_theme)}")

    # Update repos.json
    final_groups = []
    for g in original_repos:
        final_groups.append(g)

    if new_official:
        final_groups.append({
            "id": "official",
            "title": "主流大源与基础源",
            "sources": new_official
        })
    if new_community:
        final_groups.append({
            "id": "community",
            "title": "中文社区与常用源",
            "sources": new_community
        })
    if new_dev:
        final_groups.append({
            "id": "dev_extra",
            "title": "精选开发者源",
            "sources": new_dev
        })
    if new_theme:
        final_groups.append({
            "id": "theme",
            "title": "主题与美化源",
            "sources": new_theme
        })

    total_sources = sum(len(g["sources"]) for g in final_groups)
    print(f"Total sources in updated repos.json: {total_sources}")
    Path("repos.json").write_text(json.dumps(final_groups, ensure_ascii=False, indent=2), "utf-8")

    # Generate 合并越狱源.txt
    lines = [
        "# ========================================================",
        "# 越狱软件源合集（去重清洗并经可用性校验）",
        f"# 总计收录：{total_sources} 个有效源",
        "# 支持 Sileo、Zebra、Cydia、Irisin 等包管理器一键添加",
        "# ========================================================\n"
    ]

    for g in final_groups:
        lines.append(f"## 【{g['title']}】 (共 {len(g['sources'])} 个)")
        for s in g["sources"]:
            note_str = f" - {s['note']}" if s['note'] else ""
            lines.append(f"{s['url']}    # {s['name']}{note_str}")
        lines.append("")

    Path("合并越狱源.txt").write_text("\n".join(lines), "utf-8")

    # Generate 合并越狱源-纯地址.txt (方便直接复制整块)
    pure_urls = [s["url"] for g in final_groups for s in g["sources"]]
    Path("合并越狱源-纯地址.txt").write_text("\n".join(pure_urls) + "\n", "utf-8")
    print(f"Generated 合并越狱源.txt and 合并越狱源-纯地址.txt successfully!")

if __name__ == "__main__":
    build_merged()
