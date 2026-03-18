from pathlib import Path


def build_message(name: str, mood: str) -> str:
    mood_templates = {
        "开心": "祝你今天像阳光一样灿烂！",
        "难过": "愿温柔的风带走你的烦恼，慢慢好起来。",
        "紧张": "你已经很努力了，愿你从容自信、顺顺利利。",
        "平静": "愿你把这份安宁延续成一天的好心情。",
        "疲惫": "辛苦了，愿你今天也能被温柔和能量拥抱。",
    }

    template = mood_templates.get(mood.strip(), "愿你今天被温暖围绕，收获满满的小确幸！")
    return f"{name.strip()}，{template}"


def main() -> None:
    raw = input("请输入姓名和心情（例如：张三、开心）：").strip()

    name = ""
    mood = ""

    for sep in ("、", "，", ","):
        if sep in raw:
            left, right = raw.split(sep, 1)
            name = left.strip()
            mood = right.strip()
            break

    if not name:
        name = raw
    if not mood:
        mood = input("请输入心情：").strip()

    if not name:
        print("姓名不能为空，请重新运行程序后输入。")
        return

    message = build_message(name, mood)

    output_path = Path("greeting.txt")
    output_path.write_text(message, encoding="utf-8")

    print(message)
    print(f"问候语已自动保存为 {output_path.name}")


if __name__ == "__main__":
    main()
